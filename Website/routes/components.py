import requests

from utilities.component_funcs import render_server
from flask import Blueprint, render_template, request

components_bp = Blueprint("components", __name__, url_prefix="/components")


@components_bp.route("/")
def components_index():
    return "SAMonitor component endpoint"


@components_bp.get("/server-list")
def server_list():
    options = request.json()

    name = options.get("name", None),
    gamemode = options.get("gamemode", None),
    language = options.get("language", None)
    page = options.get("page", 0)

    filters = (
        f"hide_empty={options.get('hide_empty', 0)}",
        f"&hide_roleplay={options.get('hide_roleplay', 0)}",
        f"&require_sampcac={options.get('require_sampcac', 0)}",
        f"&order={options.get("order", "none")}",
        f"&page={options.get("page", 0)}",
    )

    if name:
        filters += f"&name={name}"
    if gamemode:
        filters += f"&gamemode={gamemode}"
    if language:
        filters += f"&language={language}"

    try:
        result = requests.get(f"http://127.0.0.1:42069/api/GetFilteredServers?{filters}").json()
    except:
        return """
            <center>
                <h1>Error fetching servers.</h1>
                <p>There was an error fetching servers from the SAMonitor API.</p>
                <p>This might be a server issue, in which case, an automated script has already alerted me about this. 
                Please try again in a few minutes.</p>
                <p><a href='https://status.markski.ar/'>Current status of my services</a></p>
            </center>
        """

    return render_template("components/server-list.html", servers=result, filters=filters, page=page,
                           render_server=render_server)


@components_bp.get("/server/<string:show_type>/<string:server_ip>")
def server_details(show_type, server_ip):
    if "detailed" in show_type:
        details = True
    else:
        details = False

    server_data = requests.get(f"https://sam.markski.ar/api/GetServerByIP?ip_addr={server_ip}").json()

    return render_server(server_data, details)
