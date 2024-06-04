import json
import os

import requests

# Get information from environment variables
key = os.environ.get("PANEL_API_KEY")
panel_url = os.environ.get("PANEL_URL")
plugin_name = os.environ.get("PLUGIN_NAME")
project_path = os.environ.get("PROJECT_PATH")

# Change directory to project path
os.chdir(project_path)

# Get information from deploy.json
with open("deploy.json", "r") as deploy_file:
    deploy_data = json.load(deploy_file)
    servers = deploy_data['servers']
    restart_servers = deploy_data['restart']

headers = {
    "Authorization": "Bearer " + key,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


# Method to get the plugin version from the pom.xml file
def get_version():
    version = ""
    # Get current directory
    print(os.getcwd())
    # Print all files in current directory
    print(os.listdir("."))
    print("Next")
    print(os.listdir(".."))
    with open("pom.xml", "r") as pom_file:
        for line in pom_file:
            if "<version>" in line:
                version = line.split("<version>")[1].split("</version>")[0]
                break
    return version


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
    current_directory = os.getcwd()
    files = [f for f in os.listdir(current_directory)]
    for file in files:
        print(file)

    for file in os.listdir("./target"):
        print("Found file: " + file)
        if file == plugin_name + "-" + version + ".jar":
            # Send a request to upload the file
            url = f'{panel_url}/api/client/servers/{server}/files/upload'
            response = requests.request('GET', url, headers=headers)
            upload_url = response.json()['attributes']['url']

            # Upload the file to the url
            with open("./target/" + file, "rb") as jar_file:
                r = requests.post(upload_url + "&directory=plugins", files={"files": jar_file})
                print("File uploaded, Response: " + str(r.status_code) + " " + r.text)

            return
    print("Couldn't find new jar")
    exit()


def restart_server(server):
    url = f'{panel_url}/api/client/servers/{server}/power'
    data = {
        "signal": "restart"
    }
    response = requests.request('POST', url, headers=headers, json=data)
    print("Server Restart Response: " + str(response.status_code) + " " + response.text)


# Get the plugin version from the pom.xml file
version = get_version()
if version == "":
    print("Couldn't find version")
    exit()

print("Working path: " + os.getcwd())

for server in servers:
    # Delete current jars
    delete_current_file(server)

    # Upload new jar
    get_and_upload_new_file(server)

    # Restart server if dev build
    if restart_servers:
        restart_server(server)
