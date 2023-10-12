import yaml

def deploy(chat_id,values_file):
    with open(values_file, 'r') as f:
        maas_apps = yaml.safe_load(f)

    if not next((app for app in maas_apps["applications"] if int(app) == int(chat_id)), None):
        maas_apps["applications"].append(chat_id)
    else:
        # Aborting attempt to copy existing app.
        return

    with open(values_file, "w") as f:
        yaml.dump(maas_apps, f)

def destroy(chat_id,values_file):
    with open(values_file, 'r') as f:
        maas_apps = yaml.safe_load(f)

    for row in maas_apps["applications"]:
        if int(row) == int(chat_id):
            maas_apps['applications'].remove(row)

    with open(values_file, "w") as f:
        yaml.dump(maas_apps, f)
