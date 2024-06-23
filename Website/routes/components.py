import requests

from utilities.miscfuncs import render_server, parse_datetime
from flask import Blueprint, render_template, request

components_bp = Blueprint("components", __name__, url_prefix="/components")


@components_bp.route("/")
def components_index():
    return "SAMonitor component endpoint"


@components_bp.get("/server-list")
def server_list():
    options = request.args

    name = options.get("name", None)
    gamemode = options.get("gamemode", None)
    language = options.get("language", None)
    page = int(options.get("page", 0))

    filters = ""

    if "show_empty" in options:
        filters += "&show_empty=1"

    if "hide_roleplay" in options:
        filters += "&hide_roleplay=1"

    if "require_sampcac" in options:
        filters += "&require_sampcac=1"

    if name:
        filters += f"&name={name}"
    if gamemode:
        filters += f"&gamemode={gamemode}"
    if language:
        filters += f"&language={language}"

    # Remove first ampersand for whichever option did get chosen
    if len(filters) > 0:
        filters = filters[1:]

    print(filters)

    try:
        result = (requests.get(f"http://127.0.0.1:42069/api/GetFilteredServers?{filters}&page={page}&paging_size=20")
                  .json())
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

    result_buffer = ""

    for server in result:
        result_buffer += render_server(server)

    # "Show more" button if there's more results left.
    if len(result) == 20:
        result_buffer += f"""
            <div hx-target="this" style="margin: 3rem; width: 80%; text-align: center">
                <button hx-trigger="click" hx-get="./components/server-list?{filters}&page={page + 1}" hx-swap="outerHTML">Load more</button>
            </div>
        """

    return result_buffer


@components_bp.get("/current-stats")
def current_stats():
    try:
        result = requests.get("http://127.0.0.1:42069/api/GetGlobalStats").json()
    except:
        return "<p>Failed to load stats.</p>"

    return f"""
        <p>
            <b>{"{:,}".format(result['serversOnline'])}</b> servers online (<b>{"{:,}".format(result['serversTracked'])}</b> total)<br>
            <b>{"{:,}".format(result['serversInhabited'])}</b> servers have players, 
            <b>{"{:,}".format(result['serversOnlineOMP'])}</b> have open.mp.<br>
            <b>{"{:,}".format(result['playersOnline'])}</b> are playing right now!
        </p>
    """


@components_bp.get("/server/<string:show_type>/<string:server_ip>")
def server_details(show_type, server_ip):
    if "detailed" in show_type:
        details = True
    else:
        details = False

    server_data = requests.get(f"http://127.0.0.1:42069/api/GetServerByIP?ip_addr={server_ip}").json()

    return render_server(server_data, details)


@components_bp.get("/graph/<string:server_ip>")
def server_graph(server_ip):
    hours = int(request.args.get("hours", 24))

    try:
        result = requests.get(f"http://127.0.0.1:42069/api/GetServerMetrics?hours={hours}&ip_addr={server_ip}").json()
    except:
        return "<p>Error obtaining server metrics to build graph.</p>"

    if len(result) < 3:
        return "<p>Not enough data for the activity graph, please check later.</p>"

    # Sets to feed the graph
    player_set = ""
    time_set = ""
    is_first = True

    server_metrics = list(reversed(result))

    # Minimums and maximums
    lowest = 69420
    lowest_time = None
    highest = -1
    highest_time = None

    for instant in server_metrics:
        instant_time = parse_datetime(instant['time'])

        if hours > 24:
            human_time = instant_time.strftime("%d/%m %H:%M")
        else:
            human_time = instant_time.strftime("%H:%M")

        if instant['players'] < 0:
            instant['players'] = 0

        if instant['players'] > highest:
            highest = instant['players']
            highest_time = human_time

        if instant['players'] < lowest:
            lowest = instant['players']
            lowest_time = human_time

        if is_first:
            player_set += f"{instant['players']}"
            time_set += f"'{human_time}'"
            is_first = False
        else:
            player_set += f", {instant['players']}"
            time_set += f", '{human_time}'"

    return render_template("components/graph.html", highest=highest, highest_time=highest_time,
                           lowest=lowest, lowest_time=lowest_time, time_set=time_set, player_set=player_set)


@components_bp.get("/player-list/<string:server_ip>/<int:num_players>")
def players_list(server_ip, num_players):
    if num_players > 100:
        return ("<p>There's more than 100 players in the server. "
                "Due to a SA-MP limitation, the player list cannot be fetched.</p>")

    elif num_players < 1:
        return "<p>No one is playing at the moment.</p>"

    try:
        result = requests.get(f"http://127.0.0.1:42069/api/GetServerPlayers?ip_addr={server_ip}").json()
    except:
        return "<p>Error fetching players.</p>"

    if len(result) > 0:
        # Open a table, and it's header.
        result_buffer = """
            <table style="width: 100%; border: 0;">
                <tr style="border: 1px rgb(128, 128, 128) solid">
                    <td><b>Id</b></td>
                    <td><b>Name</b></td>
                    <td><b>Score</b></td>
                    <td><b>Ping</b></td>
                </tr>
        """

        # Add a row per each player
        for player in result:
            result_buffer += f"""
                <tr>
                    <td style='width: 100px'>{player['id']}</td>
                    <td>{player['name']}</td>
                    <td>{player['score']}</td>
                    <td>{player['ping']}</td>
                </tr>
            """

        # Close the table, and return.
        result_buffer += "</table>"
        return result_buffer

    else:
        return ("<p>Could not fetch players. Server might be empty, "
                "or SAMonitor might have difficulty querying it at the moment.</p>")
