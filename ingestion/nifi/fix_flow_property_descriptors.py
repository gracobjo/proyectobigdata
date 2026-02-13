#!/usr/bin/env python3
"""
Genera un JSON de flow NiFi listo para importar en 2.7.x:
- Añade propertyDescriptors a cada procesador (evita NullPointerException).
- Añade instanceIdentifier en grupo, procesadores y conexiones (evita que solo
  aparezca 1 procesador o que falle la importación).
- Añade campos que llevan los flows exportados desde NiFi (style, bulletinLevel,
  retryCount, source/destination.instanceIdentifier, etc.).
"""
import json
import sys
import uuid
from pathlib import Path


def descriptor(prop_name, identifies_controller_service=False):
    return {
        "name": prop_name,
        "displayName": prop_name,
        "identifiesControllerService": identifies_controller_service,
        "sensitive": False,
        "dynamic": False,
    }


def ensure_processors_and_descriptors(processors):
    id_to_instance = {}
    for proc in processors:
        pid = proc.get("identifier")
        if not pid:
            continue
        if "instanceIdentifier" not in proc:
            proc["instanceIdentifier"] = str(uuid.uuid4())
        id_to_instance[pid] = proc["instanceIdentifier"]
        if "properties" in proc and "propertyDescriptors" not in proc:
            proc["propertyDescriptors"] = {
                k: descriptor(
                    k,
                    identifies_controller_service=(
                        "Service" in k or "Context" in k or "Reader" in k or "Writer" in k
                    ),
                )
                for k in proc["properties"].keys()
            }
        for key, default in (
            ("style", {}),
            ("bulletinLevel", "WARN"),
            ("runDurationMillis", 0),
            ("retryCount", 10),
            ("retriedRelationships", []),
            ("backoffMechanism", "PENALIZE_FLOWFILE"),
            ("maxBackoffPeriod", "10 mins"),
        ):
            if key not in proc:
                proc[key] = default
    return id_to_instance


def ensure_connections(connections, id_to_instance):
    for idx, conn in enumerate(connections):
        if "instanceIdentifier" not in conn:
            conn["instanceIdentifier"] = str(uuid.uuid4())
        for key, default in (
            ("labelIndex", 0),
            ("zIndex", idx + 1),
            ("prioritizers", []),
            ("bends", []),
            ("loadBalanceStrategy", "DO_NOT_LOAD_BALANCE"),
            ("partitioningAttribute", ""),
            ("loadBalanceCompression", "DO_NOT_COMPRESS"),
        ):
            if key not in conn:
                conn[key] = default
        for end in ("source", "destination"):
            if end not in conn:
                continue
            sid = conn[end].get("id")
            if sid and id_to_instance.get(sid) and "instanceIdentifier" not in conn[end]:
                conn[end]["instanceIdentifier"] = id_to_instance[sid]
            if "comments" not in conn[end]:
                conn[end]["comments"] = ""


def ensure_flow_contents(fc):
    if "instanceIdentifier" not in fc:
        fc["instanceIdentifier"] = str(uuid.uuid4())
    for key, default in (
        ("scheduledState", "ENABLED"),
        ("executionEngine", "INHERITED"),
        ("maxConcurrentTasks", 1),
        ("statelessFlowTimeout", "1 min"),
        ("flowFileConcurrency", "UNBOUNDED"),
        ("flowFileOutboundPolicy", "STREAM_WHEN_AVAILABLE"),
        ("componentType", "PROCESS_GROUP"),
    ):
        if key not in fc:
            fc[key] = default


def main():
    base = Path(__file__).parent
    input_path = base / "source" / "transport_monitoring_flow_nifi27.json"
    output_path = base / "transport_monitoring_flow_nifi27_importable.json"

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    data = json.loads(input_path.read_text(encoding="utf-8"))

    if "flowContents" not in data:
        print("No flowContents found")
        sys.exit(1)

    fc = data["flowContents"]
    ensure_flow_contents(fc)

    id_to_instance = ensure_processors_and_descriptors(fc.get("processors", []))
    ensure_connections(fc.get("connections", []), id_to_instance)

    # Estructura de root como en exportación NiFi
    if "externalControllerServices" not in data:
        data["externalControllerServices"] = {}
    if "parameterContexts" not in data:
        data["parameterContexts"] = {}
    if "parameterProviders" not in data:
        data["parameterProviders"] = {}
    if "latest" not in data:
        data["latest"] = False
    # flowEncodingVersion suele ir al final en exports
    enc = data.pop("flowEncodingVersion", "1.0")
    data["flowEncodingVersion"] = enc

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()
