import docker
import socket

try:
    client = docker.from_env()
    container_id = socket.gethostname()
    container = client.containers.get(container_id)
    print("Mounts:")
    for m in container.attrs['Mounts']:
        print(f"Source (Host): {m['Source']} -> Destination: {m['Destination']}")
except Exception as e:
    print(f"Error: {e}")
