from subprocess import Popen

def load_jupyter_server_extension(nbapp):
    """serve the notebook panel app with bokeh server"""
    Popen(["panel", "serve", "--port", "5009", "dashboard.ipynb", "--allow-websocket-origin=*"])