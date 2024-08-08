import json
import os
import sys

import requests

# Get information from environment variables
key = os.environ.get("PANEL_API_KEY")
root_folder = sys.argv[1]

# Get information from deploy.json
with open("deploy.json", "r") as deploy_file:
    deploy_data = json.load(deploy_file)
    plugin_name = deploy_data['name']
    panel_url = deploy_data['panel_url']
    servers = deploy_data['servers']
    restart_servers = deploy_data['restart']

headers = {
    "Authorization": "Bearer " + key,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def get_files_on_server(server):
    url = f'{panel_url}/api/client/servers/{server}/files/list?directory=plugins'
    response = requests.request('GET', url, headers=headers)
    json = response.json()
    return json['data']


def delete_current_file(server):
    for file in get_files_on_server(server):
        # Check if file starts with "plugin_name" and ends with ".jar"
        file_name = file['attributes']['name']
        print("Found file on server: " + file_name)
        if file_name.startswith(plugin_name) and file_name.endswith(".jar"):
            # Send a request to delete the file
            url = f'{panel_url}/api/client/servers/{server}/files/delete'
            data = {
                "root": "/plugins",
                "files": [
                    file_name
                ]
            }
            requests.request('POST', url, headers=headers, json=data)
            return
    print("No file found to delete")


def get_and_upload_new_file(server):
    libs_path = os.path.join(root_folder, "./build/libs")
    for file in os.listdir(libs_path):
        print("Found file: " + file)
        # Send a request to upload the file
        url = f'{panel_url}/api/client/servers/{server}/files/upload'
        response = requests.request('GET', url, headers=headers)
        upload_url = response.json()['attributes']['url']

        # Upload the file to the url
        with open(libs_path + file, "rb") as jar_file:
            r = requests.post(upload_url + "&directory=plugins",
                              files={"files": jar_file})
            print("File uploaded, Response: " + str(
                r.status_code) + " " + r.text)


def restart_server(server):
    url = f'{panel_url}/api/client/servers/{server}/power'
    data = {
        "signal": "restart"
    }
    response = requests.request('POST', url, headers=headers, json=data)
    print("Server Restart Response: " + str(
        response.status_code) + " " + response.text)


for server in servers:
    # Delete current jars
    delete_current_file(server)

    # Upload new jar
    get_and_upload_new_file(server)

    # Restart server if dev build
    if restart_servers:
        restart_server(server)
