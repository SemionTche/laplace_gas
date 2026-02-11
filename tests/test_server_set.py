import time
import zmq
from laplace_server.protocol import make_set_request

def test_set_gas_position(
    server_address="tcp://localhost:5555",
    target_name="GAS He",
    position=2.5
):
    """
    Test function that connects to a GAS server and sends a CMD_SET request.
    """

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(server_address)

    print(f"Connected to {server_address}")
    print(f"Sending setpoint {position} to {target_name}")

    request = make_set_request(
        "test_gas", 
        target_name, 
        positions=[position]
    )

    socket.send_json(request)

    try:
        reply = socket.recv_json()
        print("Reply received:")
        print(reply)
    except Exception as e:
        print("Error receiving reply:", e)

    socket.close()
    context.term()


if __name__ == "__main__":
    position = 2.0
    test_set_gas_position("tcp://147.250.140.65:1122", position=position)