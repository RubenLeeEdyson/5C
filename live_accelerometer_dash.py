from dash import Dash, dcc, html, Input, Output, no_update
import plotly.graph_objects as go
import pandas as pd

from cloud_credentials import CLIENT_ID, CLIENT_SECRET, THING_ID
from arduino_cloud_connection import ArduinoCloudConnection


# Arduino IoT Cloud connection

cloud = ArduinoCloudConnection(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    thing_id=THING_ID
)


# Smooth Plotly update wrapper

def smooth_extend_data(
    new_data,
    x_col="time",
    y_cols=("x", "y", "z"),
    trace_indices=(0, 1, 2),
    max_points=200
):
    """
    Prepare new continuous data for Plotly Dash extendData.

    New samples are appended to the existing Plotly traces
    instead of rebuilding the entire graph.
    """

    if new_data is None or new_data.empty:
        return no_update

    update_data = {
        "x": [
            new_data[x_col].tolist()
            for _ in y_cols
        ],
        "y": [
            new_data[col].tolist()
            for col in y_cols
        ]
    }

    return update_data, list(trace_indices), max_points


# Dash application

app = Dash(__name__)

app.layout = html.Div([
    
    html.H1("Live Smartphone Accelerometer"),

    html.Div(
        id="connection-status",
        children="Connecting to Arduino IoT Cloud..."
    ),

    dcc.Graph(
        id="accelerometer-graph",
        figure=go.Figure(
            data=[
                go.Scatter(
                    x=[],
                    y=[],
                    mode="lines",
                    name="X"
                ),
                go.Scatter(
                    x=[],
                    y=[],
                    mode="lines",
                    name="Y"
                ),
                go.Scatter(
                    x=[],
                    y=[],
                    mode="lines",
                    name="Z"
                )
            ]
        )
    ),

    dcc.Interval(
        id="update-interval",
        interval=600,
        n_intervals=0
    )
])


# Live graph callback

@app.callback(
    Output("accelerometer-graph", "extendData"),
    Output("connection-status", "children"),
    Input("update-interval", "n_intervals")
)
def update_graph(n_intervals):

    sample = cloud.get_latest_accelerometer()

    if sample is None:
        return (
            no_update,
            "Connected — waiting for new accelerometer data..."
        )

    # Convert the new sample into a DataFrame.
    new_data = pd.DataFrame([sample])

    # Prepare the incremental Plotly update.
    graph_update = smooth_extend_data(
        new_data=new_data,
        x_col="time",
        y_cols=("x", "y", "z"),
        trace_indices=(0, 1, 2),
        max_points=200
    )

    status = (
        f"Live data received | "
        f"X: {sample['x']:.2f} | "
        f"Y: {sample['y']:.2f} | "
        f"Z: {sample['z']:.2f}"
    )

    return graph_update, status


# Start Dash

if __name__ == "__main__":
    app.run(
        debug=False,
        jupyter_mode="external"
    )