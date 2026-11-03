"""Disk-backed local P31/P279 index; never a publishable dataset.

One sequential dump pass stores class edges and instance metadata. Taxonomy
review and candidate re-exports subsequently query SQLite without decompressing
the dump again. Memory usage does not grow with the entire source graph.
"""

from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from .candidates import wikipedia_sitelinks
from .dumps import iter_entities
from .local_io import atomic_text


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _fingerprint(source):
    stat = source.stat()
    return {"filename": source.name, "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
            "checksum_verified": False}


def build_index(dump_path, index_path, *, max_entities=None, progress_every=1000000):
    source, target = Path(dump_path).resolve(), Path(index_path).resolve()
    if source == target:
        raise ValueError("Index must not overwrite the source dump")
    fingerprint = _fingerprint(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=target.parent, suffix=".building.sqlite")
    os.close(descriptor)
    db = sqlite3.connect(temporary)
    count = stored = edges = 0
    try:
        db.executescript("""
            PRAGMA cache_size=-32768;
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE entities (qid TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE edges (child TEXT NOT NULL, parent TEXT NOT NULL,
                                property TEXT NOT NULL, statement TEXT NOT NULL);
        """)
        for entity in iter_entities(source, max_entities=max_entities, progress_every=progress_every):
            count += 1
            statements = []
            for prop in ("P31", "P279"):
                for claim in entity.get("claims", {}).get(prop, []):
                    if claim.get("rank") == "deprecated":
                        continue
                    value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
                    if isinstance(value, dict) and isinstance(value.get("id"), str):
                        parent = value["id"]
                        if parent.startswith("Q") and parent[1:].isdigit():
                            statements.append((entity["id"], parent, prop, _json(claim)))
            if statements:
                payload = {key: entity.get(key, {}) for key in ("labels", "descriptions")}
                payload.update(qid=entity["id"], wikipedia_sitelinks=wikipedia_sitelinks(entity))
                db.execute("INSERT INTO entities VALUES (?, ?)", (entity["id"], _json(payload)))
                db.executemany("INSERT INTO edges VALUES (?, ?, ?, ?)", statements)
                stored += 1
                edges += len(statements)
            if count % 10000 == 0:
                db.commit()
        if _fingerprint(source) != fingerprint:
            raise ValueError("Source dump changed during indexing; index discarded")
        db.executescript("""
            CREATE INDEX edges_parent ON edges(property, parent, child);
            CREATE INDEX edges_child ON edges(child, property);
        """)
        report = {"index_version": 1, "source": fingerprint, "item_entities_read": count,
                  "stored_entities": stored, "stored_statements": edges,
                  "scan_complete": max_entities is None, "max_entities": max_entities,
                  "status": "local_index_ready", "publication_allowed": False}
        db.execute("INSERT INTO metadata VALUES ('manifest', ?)", (_json(report),))
        db.commit()
        db.close()
        os.replace(temporary, target)
        return report
    finally:
        db.close()
        if os.path.exists(temporary):
            os.unlink(temporary)


def _open_index(path):
    source = Path(path).resolve()
    db = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    try:
        row = db.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()
        report = json.loads(row[0]) if row else {}
        if report.get("index_version") != 1 or report.get("status") != "local_index_ready":
            raise ValueError("Index is incomplete or has an unsupported version")
        return db, report
    except BaseException:
        db.close()
        raise


def index_taxonomy(index_path, output_path, seeds):
    """Export local agent evidence packets with an actual path to a seed."""
    if Path(index_path).resolve() == Path(output_path).resolve():
        raise ValueError("Output must not overwrite the local index")
    db, report = _open_index(index_path)
    try:
        paths = {qid: [qid] for qid in sorted(seeds)}
        queue = deque(paths)
        while queue:
            parent = queue.popleft()
            for (child,) in db.execute(
                "SELECT DISTINCT child FROM edges WHERE property='P279' AND parent=? ORDER BY child",
                (parent,),
            ):
                if child not in paths:
                    paths[child] = [child] + paths[parent]
                    queue.append(child)
        with atomic_text(output_path) as stream:
            for qid in sorted(paths):
                row = db.execute("SELECT payload FROM entities WHERE qid=?", (qid,)).fetchone()
                record = json.loads(row[0]) if row else {"qid": qid, "labels": {}, "descriptions": {}}
                record.update(
                    parent_path_qids=paths[qid],
                    p279_statements=[json.loads(row[0]) for row in db.execute(
                        "SELECT statement FROM edges WHERE child=? AND property='P279' ORDER BY parent",
                        (qid,),
                    )],
                    candidate_status="pending_agent_review", scan_complete=report["scan_complete"],
                    source=report["source"],
                )
                stream.write(_json(record) + "\n")
        return {"candidate_type_count": len(paths), "scan_complete": report["scan_complete"],
                "status": "pending_agent_review"}
    finally:
        db.close()


def index_candidates(index_path, output_path, accepted_types):
    if Path(index_path).resolve() == Path(output_path).resolve():
        raise ValueError("Output must not overwrite the local index")
    db, report = _open_index(index_path)
    try:
        # A temporary selection table avoids SQLite's variable-count limit.
        db.execute("CREATE TEMP TABLE selected_types (qid TEXT PRIMARY KEY)")
        db.executemany("INSERT INTO selected_types VALUES (?)", [(q,) for q in sorted(accepted_types)])
        count = 0
        with atomic_text(output_path) as stream:
            for qid, payload in db.execute("""
                SELECT e.qid, e.payload FROM entities e WHERE e.qid IN
                (SELECT r.child FROM selected_types t JOIN edges r ON t.qid=r.parent
                 WHERE r.property='P31') ORDER BY e.qid
            """):
                record = json.loads(payload)
                matches = [(parent, json.loads(statement)) for parent, statement in db.execute("""
                    SELECT r.parent, r.statement FROM edges r JOIN selected_types t ON t.qid=r.parent
                    WHERE r.child=? AND r.property='P31' ORDER BY r.parent
                """, (qid,))]
                record.update(matched_type_qids=sorted({p for p, _ in matches}),
                              p31_statements=[s for _, s in matches],
                              candidate_status="pending_agent_review", source=report["source"],
                              scan_complete=report["scan_complete"])
                stream.write(_json(record) + "\n")
                count += 1
        return {"candidate_entity_count": count, "scan_complete": report["scan_complete"],
                "status": "pending_agent_review"}
    finally:
        db.close()
