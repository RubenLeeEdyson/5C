import requests
from datetime import datetime


class ArduinoCloudConnection:
    """
    Connects to Arduino IoT Cloud and retrieves the latest
    smartphone accelerometer values.
    """

    TOKEN_URL = "https://api2.arduino.cc/iot/v1/clients/token"
    PROPERTIES_URL = "https://api2.arduino.cc/iot/v2/things/{}/properties"

    def __init__(self, client_id, client_secret, thing_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.thing_id = thing_id

        self.token = None
        self.last_update = None

        self.authenticate()

    def authenticate(self):
        """
        Obtain an Arduino IoT Cloud access token.
        """

        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "audience": "https://api2.arduino.cc/iot"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=10
        )

        response.raise_for_status()

        self.token = response.json()["access_token"]

        print("Arduino IoT Cloud authentication successful.")

    def get_latest_accelerometer(self):
        """
        Retrieve the latest X, Y and Z accelerometer values.

        Returns
        -------
        dict or None
            Dictionary containing time, x, y and z.
            Returns None when no new cloud value is available.
        """

        url = self.PROPERTIES_URL.format(self.thing_id)

        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        # If the token has expired, authenticate again.
        if response.status_code == 401:
            self.authenticate()

            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )

        response.raise_for_status()

        properties = response.json()

        values = {}

        for prop in properties:
            name = prop.get("variable_name")

            if name in [
                "Accelerometer_X",
                "Accelerometer_Y",
                "Accelerometer_Z"
            ]:
                values[name] = {
                    "value": prop.get("last_value"),
                    "updated_at": prop.get("value_updated_at")
                }

        required = [
            "Accelerometer_X",
            "Accelerometer_Y",
            "Accelerometer_Z"
        ]

        # Make sure all three values were found.
        if not all(name in values for name in required):
            return None

        # Use the cloud timestamp to determine whether
        # a new accelerometer value has arrived.
        timestamps = [
            values[name]["updated_at"]
            for name in required
        ]

        newest_update = max(timestamps)

        if newest_update == self.last_update:
            return None

        self.last_update = newest_update

        return {
            "time": datetime.now(),
            "x": float(values["Accelerometer_X"]["value"]),
            "y": float(values["Accelerometer_Y"]["value"]),
            "z": float(values["Accelerometer_Z"]["value"])
        }