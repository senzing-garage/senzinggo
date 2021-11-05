#! /usr/bin/env python3

import argparse
import configparser
import json
import os
import pathlib
import pwd
import re
import socket
import subprocess
import sys
import tarfile
import textwrap
import urllib
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from time import sleep

try:
    import docker
except ImportError:
    print('\nPlease install the Python Docker module (pip3 install docker)\n')
    sys.exit(1)

__all__ = []
__version__ = '1.3.0'  # See https://www.python.org/dev/peps/pep-0396/
__date__ = '2021-09-10'
__updated__ = '2021-11-04'


class Colors:
    HEAD = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARN = '\033[93m'
    ERROR = '\033[91m'
    BOLD = '\033[1m'
    COLEND = '\033[0m'


# Documentation
# -------------

# Docker on same machine
# Firewall allow local machine to connect but not external
# Document using it in quick start and update qs
#   Swagger and curl and gui tools too
# Note about purging
# Warning that accessible to outside host
# Not meant or production, basic local stack for demo/dev/test

# TO CONSIDER
# -----
# Make script work to do a package without other requirements like G2Path
# Arg to use another registry other than Docker Hub
# Add support for MSSQL
# Use env var settings to override default command
#   https://github.com/Senzing/docker-compose-demo/blob/291142de3c33e82ee658f0b411c77cd88921ee44/resources/postgresql/docker-compose-rabbitmq-postgresql.yaml#L229-L231
# SSL/HTTPS


def get_senzing_root(script_name):
    """ Get the SENZING_ROOT env var """

    senz_root = os.environ.get('SENZING_ROOT', None)

    if not senz_root:
        if os.geteuid() == 0:
            print(
                f'\n{Colors.ERROR}ERROR:{Colors.COLEND} Running with sudo. Ensure the setupEnv file is sourced and run with: sudo --preserve-env ./{script_name}')
            sys.exit(1)

        print(f'\n{Colors.ERROR}ERROR:{Colors.COLEND} SENZING_ROOT isn\'t set please source the project setupEnv file')
        sys.exit(1)

    return senz_root


def get_host_name():
    """ Attempt to get fully qualified hostname or IP"""

    # FQDN
    host_name = socket.getfqdn(socket.gethostbyname(socket.gethostname()))

    # Hostname
    if not host_name:
        host_name = socket.gethostbyname(socket.gethostname())

    # Otherwise set to localhost, can be overridden with the -ho CLI arg
    if not host_name:
        print(textwrap.dedent(f'''\n\
            {Colors.WARN}WARNING:{Colors.COLEND} Unable to detect a hostname, using 127.0.0.1., this could cause issues.
                                  
                     If networking issues arise please set a true hostname or try using the --host (-ho) argument
                     to specify host or ip address.
                '''))
        host_name = '127.0.0.1'
        sleep(3)

    return host_name


def ini_localhost_check(ini_file_name):
    """ Check the INI file doesn't use localhost
        localhost can't be used when the INI file is baked into a container, would be pointing to the container itself
    """

    with open(ini_file_name, 'r') as inifile:
        for line in inifile:
            line_check = line.lstrip().lower()

            # Look for localhost in normal and cluster ini lines
            if (line_check.startswith('connection') or line_check.startswith('db_1')) and (
                    '@localhost:' in line_check or '@127.0.0.1:' in line_check):
                print(textwrap.dedent(f'''\n\
                    {Colors.ERROR}ERROR:{Colors.COLEND} Connection string cannot use localhost or 127.0.0.1, use a true hostname or ip address
                           {line}
                '''))
                sys.exit(1)


def convert_ini2json(ini_file_name):
    """ Convert INI parms to JSON for use in the Docker containers"""

    ini_json = {}

    cfgp = configparser.ConfigParser()
    cfgp.read(ini_file_name)

    for section in cfgp.sections():
        ini_json[section] = dict(cfgp.items(section))

    return ini_json


def internet_access(url, retries=3, retries_start=None, tout=2, check_msg=True):
    """ Test for access to resources that are required"""

    if check_msg:
        print(f'\n\t{url}', end='', flush=True)

    try:
        urllib.request.urlopen(url, timeout=tout)
        print(f'{Colors.GREEN} Available{Colors.COLEND}', end='')
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout):
        if retries > 1:
            print('.', end='', flush=True)
            retries -= 1
            retries_start = retries if not retries_start else retries_start
            sleep(1)
            internet_access(url, retries, retries_start, check_msg=False)

    if retries == retries_start:
        print(f'{Colors.WARN} Unavailable{Colors.COLEND}', end='')

    return False


def get_api_spec(url, retries=3, tout=3):
    """ Get the REST API specification from the REST server """

    try:
        api_spec_url = urllib.request.urlopen(url, timeout=tout)
        api_spec = api_spec_url.read()
        return api_spec
    except (urllib.error.URLError, urllib.error.HTTPError) as ex:
        while retries > 1:
            print('.', end='', flush=True)
            retries -= 1
            sleep(3)
            get_api_spec(url, retries)

        print(textwrap.dedent(f'''\n
                {Colors.ERROR}ERROR:{Colors.COLEND} Unable to get API specification from Senzing REST server, cannot continue!
                       {ex}
                '''))

        sys.exit(1)


def parse_versions(url):
    """ Parse the online Senzing Docker versions file into a dict to looking latest version numbers"""

    # #!/usr/bin/env bash
    #
    # # Generated on 2021-10-05 by https://github.com/Senzing/dockerhub-util dockerhub-util.py version: 1.0.3 update: 2021-10-05
    #
    # export SENZING_DOCKER_IMAGE_VERSION_ADMINER=1.0.0
    # export SENZING_DOCKER_IMAGE_VERSION_APT=1.0.5.post1
    # export SENZING_DOCKER_IMAGE_VERSION_APT_DOWNLOADER=1.1.3

    try:
        # Read the versions data into a dict
        response = urllib.request.urlopen(url)
        page = response.read().decode().replace('export SENZING_', 'SENZING_')
        versions = {kv.split('=')[0]: kv.split('=')[1] for kv in
                    [line for line in page.split('\n') if line.startswith('SENZING_')]}
    except urllib.error.HTTPError as ex:
        print(textwrap.dedent(f'''\n\
            {Colors.ERROR}ERROR:{Colors.COLEND} Fetching latest versions, the server couldn't fulfill the request.
                   Error code: {ex.code})
        '''))
        return False
    except urllib.error.URLError as ex:
        print(textwrap.dedent(f'''\n\
            {Colors.ERROR}ERROR:{Colors.COLEND} Fetching latest versions, failed to reach a server.
                   Reason: {ex.reason})
        '''))
        return False

    return versions


def docker_checks(script_name):
    """ Perform checks for Docker """

    print('\nPerforming Docker checks...\n', flush=True)

    # Is Docker installed?
    try:
        dversion = subprocess.run(['docker', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  encoding='utf8')
        if 'podman' in dversion.stdout.lower():
            print(textwrap.dedent(f'''\n
                {Colors.ERROR}ERROR:{Colors.COLEND} Podman is being used instead of Docker, this is unsupported this tool requires Docker
                       https://docs.docker.com/engine/install/
            '''))
            sys.exit(1)
    except FileNotFoundError:
        print(textwrap.dedent(f'''\n\
                {Colors.ERROR}ERROR:{Colors.COLEND} Docker doesn\'t appear to be installed and is required
                       https://docs.docker.com/engine/install/
            '''))
        sys.exit(1)

    # Not launched as sudo, check if user can use docker without sudo
    if os.geteuid() != 0:

        # Will succeed if the user can use docker without sudo - e.g. in the docker group, docker running rootless
        check = subprocess.run(['docker', 'images'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf8')

        if check.returncode != 0:
            if 'permission denied' and 'socket' in check.stderr:
                print(
                    f'\n{Colors.ERROR}ERROR:{Colors.COLEND} User cannot run Docker, you need to run with sudo --preserve-env ./{script_name} or be added to the docker group...\n')
            else:
                print(f'\n{Colors.ERROR}ERROR:{Colors.COLEND} {check.stderr}')
            sys.exit(1)

    if os.geteuid() == 0 and 'SENZING_ROOT' not in os.environ:
        print(f'SENZING_ROOT isn\'t set please source setupEnv and run with: sudo --preserve-env ./{script_name}')
        sys.exit(1)


def docker_init():
    """ Initialise a Docker client """

    try:
        client = docker.from_env()
    except docker.errors.DockerException as ex:
        print(textwrap.dedent(f'''\n\
            {Colors.ERROR}ERROR:{Colors.COLEND} Unable to instantiate Docker, is the Docker service running?
                   {ex}
        '''))
        sys.exit(1)

    return client


def docker_image_exists(docker_client, image_name):
    """ Test if a Docker image already exists """

    return True if docker_client.images.list(name=image_name) else False


def pull_default_images(docker_client, docker_containers, no_web_app, no_swagger):
    """ Docker pull the base set of images required for the tool
        Senzing Rest API server, Senzing Entity Search App, Swagger UI
    """

    print('\nChecking and pulling Docker images, this may take many minutes...\n')

    for key, image_list in docker_containers.items():

        # Skip pulling images if CLI args request not to deploy
        if no_web_app and image_list['imagename'] == 'senzing/web-app-demo':
            continue

        if no_swagger and image_list['imagename'] == 'swaggerapi/swagger-ui':
            continue

        image_with_version = image_list['imagename'] + ':' + image_list['tag']

        did_pull = docker_pull(docker_client, image_with_version)
        if not did_pull and key == 'restapi':
            print(
                f'\n{Colors.ERROR}ERROR:{Colors.COLEND} Couldn\'t pull REST API Server image, can\'t continue without it!')
            sys.exit(0)
        elif did_pull == 'PULLED':
            docker_containers[key]['imagepulled'] = True

        docker_containers[key]['imageavailable'] = True


def docker_pull(docker_client, image):
    """ Pull Docker images """

    if not docker_image_exists(docker_client, image):
        print(f'\n\tPulling {image}...', flush=True)

        try:
            docker_client.images.pull(image)
            return 'PULLED'
        except (docker.errors.ImageNotFound, docker.errors.NotFound) as ex:
            print(f'\t{ex}')
            return False
    else:
        print(f'\t{image} exists, not pulling', flush=True)

    return True


def docker_net(docker_client, network_name, network_driver='bridge'):
    """ Create a Docker network for use by the project containers """

    if not docker_client.networks.list(names=network_name):
        print(f'Docker network {network_name} doesn\'t exist, creating...\n')

        try:
            docker_client.networks.create(name=network_name, driver=network_driver)
        except docker.errors.DockerException as ex:
            print(f'{ex}')
            sys.exit(1)


def docker_cont_list(docker_client, all_conts=True, cont_filters={}):
    """ Get a list of the current Docker containers """

    return docker_client.containers.list(all=all_conts, filters=cont_filters)


def docker_run(docker_client, docker_containers, **kwargs):
    """ Create and run a container """

    def status_wait(msg, check, cont_name, loop_cnt=20, t_sleep=5):
        """ Wait for container to become healthy if it reports health """

        print(f'\n\t{msg}', end='', flush=True)

        for r in range(loop_cnt):
            cont_status = docker_client.containers.get(cont_name).status
            cont_attrs = docker_client.containers.get(cont_name).attrs

            if check == 'running' and cont_status == 'running':
                return check

            if check == 'healthy' and cont_attrs['State']['Health']['Status'] == 'healthy':
                return check

            sleep(t_sleep)
            print('.', end='', flush=True)
        print()

        cont_status = docker_client.containers.get(cont_name).status
        cont_attrs = docker_client.containers.get(cont_name).attrs

        return cont_status if check == 'running' else cont_attrs['State']['Health']['Status']

    def docker_logs(cont):
        """ Dump Docker logs for a container """

        if cont:
            print(f'{Colors.WARN}\n********** Start Docker Logs **********\n{Colors.COLEND}')
            print(cont.logs().decode())
            print(f'{Colors.WARN}\n********** End Docker Logs **********\n{Colors.COLEND}')

    # Get the container key to use at the end to set startedok status
    container_key = kwargs['container']

    # Remove the container key from the args sent to the run, only used to set startedok
    del kwargs['container']

    print(f'\nRunning {kwargs["image"]}...')

    try:
        docker_client.containers.run(**kwargs)
    except docker.errors.APIError as ex:
        print(f'\n{Colors.ERROR}ERROR:{Colors.COLEND} {ex}')
        sys.exit(1)

    if status_wait(f'Waiting for container to start.',
                   'running',
                   kwargs['name']
                   ) == 'exited':
        print(
            f'\n\t{Colors.ERROR}ERROR:{Colors.COLEND} Container did not start successfully, status: {docker_client.containers.get(kwargs["name"]).status}')
        docker_logs(docker_client.containers.get(kwargs['name']))
        sys.exit(1)

    # Container might not have HEALTHCHECK set in Docker file, if it does wait for it to become healthy
    if docker_client.containers.get(kwargs['name']).attrs.get('State').get('Health', None):
        if status_wait('Waiting for container to become healthy.',
                       'healthy',
                       kwargs['name']
                       ) != 'healthy':
            print(
                f'\n\t{Colors.WARN}WARNING:{Colors.COLEND} Container isn\'t healthy yet or failed, monitor with the command "docker logs {kwargs["name"]}"')
            docker_logs(docker_client.containers.get(kwargs['name']))
    else:
        print('\n\tThis container doesn\'t report health')
        print(f'\tUse the command "docker logs {kwargs["name"]}" to check status if issues arise ')

    docker_containers[container_key]['startedok'] = True


def containers_stop_remove(senzing_proj_name,
                           docker_client,
                           docker_containers,
                           containers_remove,
                           containers_remove_no_prompt,
                           docker_network,
                           startup_remove=False,
                           forced_remove=False):
    """ Stop and optionally remove SenzingGo containers """

    # Only lists running containers, all=True to return all
    print(f'Looking for existing containers to remove...\n')

    # Look for containers that match the project name, including any that are not running (all=True)
    containers = docker_cont_list(docker_client, all_conts=True, cont_filters={'name': senzing_proj_name})

    # Base project container names
    project_container_names = [values['containername'] for values in docker_containers.values()]
    running_containers = [c.attrs['Name'].lstrip('/') for c in containers]

    # Don't print message if in startup and deleting any existing containers
    if not running_containers and not startup_remove:
        print(
            f'No matching containers for {senzing_proj_name}, were the containers created with a different suffix with -p (--projectSuffix)?')
        all_containers = docker_cont_list(docker_client, all_conts=True)
        if all_containers:
            print('\nAvailable containers:\n')
            for cont in all_containers:
                print(f'\t{cont.attrs["Name"].lstrip("/")}')
        return

    # Are you really sure you want to remove
    if containers_remove:
        spacer = '\n\t'
        print(f'{Colors.WARN}WARNING:{Colors.COLEND} Are you sure you want to delete the following containers? (Y/n):')
        print(f'{spacer}{spacer.join(c for c in running_containers)}')

        if not input() in ['', 'y', 'Y', 'yes', 'YES']:
            sys.exit(0)

    for cont in containers:
        # Remove leading / https://github.com/docker/docker-py/pull/2634
        cont_name = cont.attrs['Name'].lstrip('/')

        if cont_name in project_container_names:
            print(f'\t{cont_name}')
            print('\t\tStopping...')

            try:
                cont.stop()
            except docker.errors.APIError as ex:
                print(textwrap.dedent(f'''\n\
                    {Colors.ERROR}ERROR:{Colors.COLEND} Failed to stop container
                           {ex}
                '''))

            if containers_remove or containers_remove_no_prompt or startup_remove or forced_remove:
                print('\t\tRemoving...\n')
                try:
                    # Remove volumes too
                    cont.remove(v=True, force=True)
                except docker.errors.APIError as ex:
                    print(ex)
            else:
                print()

    # Remove the network too
    if containers_remove or containers_remove_no_prompt:
        network_list = docker_client.networks.list(names=docker_network)

        # Should only be one item in the list as use names filter above on the network for the project
        if network_list:
            print(f'\nRemoving Docker network {network_list[0].attrs["Name"]}')
            with suppress(Exception):
                network_list[0].remove()


def containers_info(docker_client, docker_containers, senzing_proj_name, host_name):
    """ Get info for running containers, e.g. the url they are running on after startup information is lost """

    print(f'\nLooking for containers matching {senzing_proj_name}...')

    containers = docker_cont_list(docker_client, all_conts=True, cont_filters={'name': senzing_proj_name})

    if not containers:
        print(f'\nThere are currently no containers matching {senzing_proj_name}')
        sys.exit(0)

    for name in [c.name for c in containers]:

        # name is used as a key in the NetworkSettings -> Ports JSON object and is needed to find the host port the container
        # was started on
        if name.startswith('SzGo-API-'):
            key = 'restapi'
        elif name.startswith('SzGo-WEB-'):
            key = 'webapp'
        elif name.startswith('SzGo-Swagger-'):
            key = 'swagger'
        else:
            # Only continue and list info for SenzingGo containers
            print(f'\nMatching containers found for {senzing_proj_name}, but they don\'t appear to be for SenzingGo')
            sys.exit(0)

        status = docker_client.containers.get(name).attrs.get("State")["Status"]
        print(f'\nContainer: {name}\n')
        print(f'\tImage:  {docker_client.containers.get(name).attrs.get("Config").get("Image")}')
        print(f'\tStatus: {status}')
        if status == 'running':
            host_port = docker_client.containers.get(name).attrs.get("NetworkSettings").get("Ports")[
                str(docker_containers[key]["containerport"]) + "/tcp"][0]["HostPort"]
            print(f'\tURL:    http://{host_name}:{host_port}')

    sys.exit(0)


def container_logs(docker_client, logs_string=None):
    """ Get logs for one or more containers """

    # Using filter there could be more than one container returned
    matching_containers = docker_cont_list(docker_client,
                                           cont_filters={"name": logs_string if logs_string else 'SzGo'})

    if matching_containers:
        for cont in matching_containers:
            print(f'\n{Colors.GREEN}********** Start logs for {cont.name} **********{Colors.COLEND}')
            print(f'\n{cont.logs().decode()}')
            print(f'\n{Colors.GREEN}********** End logs for {cont.name} **********\n{Colors.COLEND}')
    else:
        print('\nNo matching container(s) to show logs for, use -i (--info) to see available containers\n')

    sys.exit(0)


def list_image_names(docker_image_names, access, versions):
    """ Get a list of all Senzing image names, used when packaging a custom save images file """

    if not access:
        print(f'\n{Colors.ERROR}ERROR:{Colors.COLEND} Unable to obtain the list of Senzing Docker images to display')
        sys.exit(1)
    print()

    try:
        # Read the docker images json file from github
        response = urllib.request.urlopen(docker_image_names)
        page = response.read().decode()
    except urllib.error.HTTPError as ex:
        print(textwrap.dedent(f'''\n\
            {Colors.BLUE}INFO:{Colors.COLEND} Fetching image names, the server couldn't fulfill the request.
                  Error code: {ex.code})
            '''))
        return False
    except urllib.error.URLError as ex:
        print(textwrap.dedent(f'''\n\
            {Colors.BLUE}INFO:{Colors.COLEND} Fetching image names, failed to reach a server.
                  Reason: {ex.reason}
            '''))
        return False

    docker_image_names = json.loads(page)

    if not versions:
        print('Using "latest" for version, the versions file wasn\'t available for reference')
    print()

    # Display the image name (k) and either the version number if available or latest
    for k, v in docker_image_names.items():
        print(f'{k}:{versions.get(v["environment_variable"], "latest") if versions else "latest"}')


def get_timestamp():
    """ Create timestamp """

    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_images(docker_client, docker_containers, save_images, save_images_path, access_dockerhub, no_web_app,
                no_swagger, senzing_proj_name):
    """ Package up base set or custom set of images to transfer and use on another system """

    avail_images_with_tag = []
    packaged_files = []

    # Set package path depending on if default value (str) was used or a path was specified (list)
    package_path = save_images_path[0] if isinstance(save_images_path, list) else save_images_path

    if not access_dockerhub:
        print(
            f'\n{Colors.WARN}WARNING:{Colors.COLEND} Cannot reach internet to pull images, can only package existing ones if available.')

    # If a list of packages was specified pull them, otherwise no arguments on saveimages arg
    if len(save_images) > 0:

        # If have internet access perform pull
        # If don't have internet access check if each image exists, if it doesn't error as can't complete the request
        for image in save_images:
            if access_dockerhub:
                docker_pull(docker_client, image)

            try:
                docker_client.images.get(image)
            except docker.errors.ImageNotFound:
                print(
                    f'\n{Colors.ERROR}ERROR:{Colors.COLEND} Image {image} isn\'t available to save, can\'t complete request.')
                sys.exit(1)

            avail_images_with_tag.append(image)

    # Normal packaging of the base images needed for rest, webapp, swagger
    else:
        images_newest_dict = {}
        if access_dockerhub:
            pull_default_images(docker_client, docker_containers, no_web_app, no_swagger)

        # Get a list of all images, only get the first tag entry [0] if there are > 1 tags
        images = [i.tags[0] for i in docker_client.images.list()]
        images.sort()

        # Use a dict to store only one image with the latest version from the sort, sort has latest version first
        # There could be multiple versions of an image on a system from earlier use or manual pulls, get the latest one
        for image in images:
            # There could be an image tagged to push to a local registry, e.g. localhost:5000/senzing/senzing-api-server:2.7.5
            # ignore these
            if image.count(':') > 1:
                continue
            name, version = image.split(':')
            images_newest_dict[name] = version

        # Join the image name and version back into a unique list of images to package up
        avail_to_package = [k + ':' + v for k, v in images_newest_dict.items()]

        # If an image name without the tag is in the base set of images add it to be packaged
        # In this packaging mode only want the 3 base images
        for candidate_image in avail_to_package:
            if candidate_image.split(':')[0] in (docker_containers['restapi']['imagename'],
                                                 docker_containers['webapp']['imagename'],
                                                 docker_containers['swagger']['imagename']):
                avail_images_with_tag.append(candidate_image)

    if not avail_images_with_tag:
        print(f'\n{Colors.ERROR}ERROR:{Colors.COLEND} There are no images to save')
        sys.exit(1)

    # Write each image out to a file, named as the image with / and : replaced with -
    # The Docker API doesn't support saving multiple images to a single tar like native docker save command
    for image in avail_images_with_tag:
        package_file = f'{package_path}/SzGoPackage-{image.replace("/", "-").replace(":", "-")}.tar'
        packaged_files.append(package_file)

        try:
            with open(package_file, 'wb') as sf:
                image_to_save = docker_client.images.get(image)
                print(f'\nSaving {image} to {package_file}...')
                for chunk in image_to_save.save(named=True):
                    sf.write(chunk)
        except FileNotFoundError as ex:
            print(f'\n{Colors.ERROR}ERROR:{Colors.COLEND} {ex}')
            sys.exit(1)

    compressed_package = f'{package_path}/SzGoImages-{senzing_proj_name}_{get_timestamp()}.tgz'
    print(f'\nCompressing saved images to {compressed_package}, this will take several minutes...')

    # Add the image tar files to compressed tar and delete the image tar files
    try:
        with tarfile.open(compressed_package, 'w:gz') as tar:
            for name in packaged_files:
                # arcname to specify only the file name to tar not the entire dir structure
                tar.add(name, recursive=False, arcname=Path(name).name)
                os.remove(name)
    except FileNotFoundError as ex:
        print(f'\n{Colors.ERROR}ERROR:{Colors.COLEND} {ex}')
        sys.exit(1)

    print(textwrap.dedent(f'''\n\
        Move {compressed_package} to the system to load the images to and run this tool with --loadImages (-li)
    '''))


def load_images(docker_client, var_path, load_file_path):
    """ Load images that have previously been packaged up with save images """

    extract_path = var_path / f'SzGo_Extract_{get_timestamp()}'
    file_to_extract = Path(load_file_path).resolve()

    # Uncompress tar file to retrieve the tar image files
    print(f'Extracting Senzing Docker images from {file_to_extract}...')

    try:
        with tarfile.open(file_to_extract, 'r:gz') as tar:
            tar.extractall(path=extract_path)
    except FileNotFoundError as ex:
        print(f'\n{Colors.ERROR}ERROR:{Colors.COLEND} {ex}')
        sys.exit(1)

    for image_file in os.scandir(extract_path):
        print(f'\tLoading image file {image_file.name}')
        try:
            with open(image_file, 'rb') as lf:
                docker_client.images.load(lf)
        except FileNotFoundError as ex:
            print(f'\n{Colors.ERROR}ERROR:{Colors.COLEND} {ex}')
            sys.exit(1)

    # Once completed remove the temp extract dir
    with suppress(Exception):
        os.remove(extract_path)


def patch_ini_json(ini_json):
    """ Patch the INI file for use inside of container """

    def type_connection_split(connection_string):
        """ """

        try:
            dbtype, connection = connection_string.split(':', 1)
        except ValueError:
            print(textwrap.dedent(f'''\n\
                {Colors.ERROR}ERROR:{Colors.COLEND} Couldn\'t parse connection string and find the database type:
                       {connection_string}'
            '''))
            sys.exit(1)

        return dbtype, connection

    def get_path(connection_string):
        """ """

        _, connection = type_connection_split(connection_string)

        try:
            _, conn_str = connection.split('@', 1)
        except ValueError:
            print(textwrap.dedent(f'''\n\
                {Colors.ERROR}ERROR:{Colors.COLEND} Couldn\'t parse connection string on @:
                       {conn_str}
            '''))
            sys.exit(1)

        conn_str_path = Path(conn_str).resolve().parent

        return str(conn_str_path)

    # Correct ini parms for inside container and volume args on docker run command(s)
    ini_json['PIPELINE']['supportpath'] = '/opt/senzing/data'
    ini_json['PIPELINE']['configpath'] = '/etc/opt/senzing'
    del ini_json['PIPELINE']['resourcepath']

    # Get the base connection string regardless of clustered mode or not
    base_conn_str = ini_json['SQL']['connection']

    dbtype, connection = type_connection_split(base_conn_str)

    if dbtype.lower() == 'sqlite3':

        # If a cluster check each sqlite db file is in the same path, needed for mounting into Docker API server container
        # This tool doesn't support each db file in different locations
        if ini_json['SQL'].get('backend', None) and ini_json['SQL']['backend'].lower() == 'hybrid':

            # Get the unique set of cluster keys used in the ini [HYBRID] section, e.g. C1, C2
            cluster_keys = [ini_json['HYBRID'][cluster_key] for cluster_key in ini_json['HYBRID']]
            unique_cluster_keys = list(set(cluster_keys))

            # Get all the connection strings for each cluster key detected in [HYBRID], add base connection too
            # e.g. sqlite3://na:na@/home/ant/senzprojs/2_7_0-Release/var/sqlite/G2_RES.db
            cluster_conn_strs = [ini_json[cluster_key]['db_1'] for cluster_key in unique_cluster_keys]
            cluster_conn_strs.append(base_conn_str)

            # Get the path without the database file name for each connection string
            # e.g. /home/ant/senzprojs/2_7_0-Release/var/sqlite
            path_list = [get_path(path) for path in cluster_conn_strs]
            unique_path_list = list(set(path_list))

            if len(unique_path_list) > 1:
                print(f'\nWhen using a sqlite cluster, all database files must be in the same path:')
                for path in unique_path_list:
                    print(f'\t{path}')
                sys.exit(1)

            # The host path to mount in the docker run volume arg is the only value on the list after it was made unique
            host_path_for_volume = unique_path_list[0]

        # Not clustered
        else:
            host_path_for_volume = get_path(base_conn_str)

        # Replace the original path(s) with the path inside the container
        json_str = json.dumps(ini_json)
        ini_json_patched = json.loads(json_str.replace(host_path_for_volume, '/var/opt/senzing'))

        # Build the values to use in the volume argument for the mount to return
        mount_in_cont = [host_path_for_volume, {"bind": "/var/opt/senzing", "mode": "rw"}]

        return dbtype, ini_json_patched, mount_in_cont

    # If not sqlite return the patched ini_json without meddling with connection strings
    return dbtype, ini_json, None


def mysql_check(senzing_root, lib_my_sql, db_type, senzing_support):
    """ Checks for MySql """

    lib_mysql_path = Path(f'{senzing_root}/lib/{lib_my_sql}')

    if not lib_mysql_path.is_file():
        print(textwrap.dedent(f'''\n\
                                  {Colors.WARN}WARNING:{Colors.COLEND} To use MySQL with this tool {lib_my_sql} is required to be in {senzing_root}/lib/ 
                                           This allows the API server to use it inside the container. Senzing cannot distribute 
                                           this file, to use Senzing with MySQL this must be user installed.
                                            
                                           {lib_my_sql} may already be installed in this machine if you have installed the MySQL 
                                           client. You can check with: 
                                            
                                               sudo find / -name "libmysqlclient*" 
                                               
                                           If located, copy {lib_my_sql} to {senzing_root}/lib/, for example:
                                           
                                               cp /lib/x86_64-linux-gnu/libmysqlclient.so.21 {senzing_root}/lib/libmysqlclient.so.21
                                               
                                           If {lib_my_sql} wasn't found install the MySQL client libraries appropriate for your distribution and create
                                           the copy as above. For example, on Debian based systems:
                                           
                                               sudo apt install libmysqlclient21
                                               
                                           {senzing_support} 
        '''))
        sys.exit(1)

    print(
        f'\n{Colors.BLUE}INFO:{Colors.COLEND} Database type is {db_type} and {lib_my_sql} is available in {senzing_root}/lib')


def db2_check(args, senzing_support):
    """ Check for Db2 """

    try:
        db2_cli_path = args.db2CliPath[0]
    except TypeError:
        print(textwrap.dedent(f'''\n\
            {Colors.WARN}WARNING:{Colors.COLEND} When the database type is Db2 use the --db2CliPath (-db2c) argument to specify the
                     location on this machine of the Db2 client CLI drivers. This allows the API server 
                     to use them inside the container. Senzing cannot distribute this installation, to
                     use Senzing with Db2 this must be user installed. 
                     
                     This path should be the location of the Db2 client CLI drivers where the directories
                     such as /cfg and /lib are located, for example:
                     
                        /opt/IBM/db2_cli_odbc_driver/odbc_cli/clidriver
                        
                     https://www.ibm.com/docs/en/db2/11.5?topic=clients-data-server-drivers
                     
                     {senzing_support}
        '''))

        sys.exit(1)

    db2_cli_path_lib = Path(f'{db2_cli_path}/lib')
    db2_cli_cfg_file = Path(f'{db2_cli_path}/cfg/db2dsdriver.cfg')

    if not db2_cli_path_lib.is_dir():
        print(textwrap.dedent(f'''\n\
            {Colors.ERROR}ERROR:{Colors.COLEND} {str(db2_cli_path)} doesn't appear to contain the expected directories such as /cfg 
                   and /lib
                   
                   Is {str(db2_cli_path)} the path that contains the Db2 client CLI drivers and  
                   directories such as /cfg and /lib?
                   
                   {senzing_support}
        '''))

        sys.exit(1)

    if not db2_cli_cfg_file.is_file():
        print(textwrap.dedent(f'''\n\
            {Colors.ERROR}ERROR:{Colors.COLEND} {str(db2_cli_cfg_file)} doesn't appear to exist and is required.
                                  
                   {senzing_support}
        '''))

        sys.exit(1)

    with open(db2_cli_cfg_file, 'r') as cfgfile:
        for line in cfgfile:
            line_check = line.lstrip().lower()

            # Look for localhost in alias and name cfg lines
            if (line_check.startswith('<dsn alias=') or line_check.startswith('<database name=')) and (
                    'localhost' in line_check or '127.0.0.1' in line_check):
                print(textwrap.dedent(f'''\n\
                    {Colors.ERROR}ERROR:{Colors.COLEND} Host in the db2dsdriver.cfg file cannot use localhost or 127.0.0.1, use a true hostname or ip address
                           {line.lstrip()}
                '''))
                sys.exit(1)


def package_msg():
    """ Message for packaging """

    print(textwrap.dedent(f'''\n\
        {Colors.BLUE}INFO:{Colors.COLEND} This tool can be used on another system with internet access and Docker to package up the required Docker 
              images. This package can subsequently be used on this (or other machines) to make the required Docker images 
              available for use.
              
              See --help" and the --saveImages (-si) and --loadImages (-li) arguments.        
        '''))


def get_senzing_proj_name(root_path):
    """ Get the project name from root path running in """

    # Keep only valid chars from the project name for use in the suffix for containers
    # Valid chars in reference to Docker container names
    chars_remove = re.compile('[^a-zA-Z0-9_.-]')
    proj_name_clean = chars_remove.sub('', root_path)

    if root_path != proj_name_clean:
        print(
            f'\n{Colors.BLUE}INFO:{Colors.COLEND} Container names will use the suffix {proj_name_clean} instead of {root_path}')
        return proj_name_clean

    return root_path


def main():
    """ """

    SCRIPT_NAME = Path(__file__).name
    SCRIPT_STEM = Path(__file__).stem

    # URLs for required assets
    DOCKER_LATEST_URL = 'https://raw.githubusercontent.com/Senzing/knowledge-base/master/lists/docker-versions-latest.sh'
    DOCKERHUB_URL = 'https://hub.docker.com/u/senzing/'
    DOCKER_IMAGE_NAMES = 'https://raw.githubusercontent.com/Senzing/knowledge-base/master/lists/docker-image-names.json'
    # SENZING_AIR_GAP_INSTALL = 'https://senzing.zendesk.com/hc/en-us/articles/360039787373-Install-Air-Gapped-Systems'

    # Check setup env has been run and determine project name from path
    SENZING_ROOT = get_senzing_root(SCRIPT_NAME)
    SENZING_ROOT_PATH = pathlib.PurePath(SENZING_ROOT)
    SENZING_VAR_PATH = SENZING_ROOT_PATH / 'var'
    senzing_proj_name = get_senzing_proj_name(SENZING_ROOT_PATH.name)

    SZGO_REST_JSON = 'SzGo-rest-api.json'
    SZGO_REST_SPEC = 'specifications/open-api'

    LIB_MY_SQL = 'libmysqlclient.so.21'

    SENZING_SUPPORT = 'For further assistance contact support@senzing.com'
    SZGO_HELP ='https://github.com/Senzing/senzinggo'

    # Dict of the containers required and details to use, names match project path/name to allow >1 project and containers
    docker_containers = \
        {'restapi':
            {
                'imagename': 'senzing/senzing-api-server',
                'latestsuffix': 'SENZING_DOCKER_IMAGE_VERSION_SENZING_API_SERVER',
                'containername': f'SzGo-API-{senzing_proj_name}',
                'containerport': 8250,
                'hostport': 8250,
                'imagepulled': False,
                'imageavailable': None,
                'tag': None,
                'startedok': None
            },
         'webapp':
            {
                'imagename': 'senzing/entity-search-web-app',
                'latestsuffix': 'SENZING_DOCKER_IMAGE_VERSION_ENTITY_SEARCH_WEB_APP',
                'containername': f'SzGo-WEB-{senzing_proj_name}',
                'containerport': 8081,
                'hostport': 8251,
                'imagepulled': False,
                'imageavailable': None,
                'tag': None,
                'startedok': None
            },
         'swagger':
            {
                'imagename': 'swaggerapi/swagger-ui',
                'latestsuffix': 'SENZING_DOCKER_IMAGE_VERSION_SWAGGERAPI_SWAGGER_UI',
                'containername': f'SzGo-Swagger-{senzing_proj_name}',
                'containerport': 8080,
                'hostport': 9180,
                'imagepulled': False,
                'imageavailable': None,
                'tag': None,
                'startedok': None
            }
         }

    # Attempt to get hostname / IP of machine where running
    host_name = get_host_name()

    # Don't allow argparse to create abbreviations of options
    szgo_parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, allow_abbrev=False)

    szgo_parser.add_argument('-c', '--iniFile', default=None, nargs=1,
                             help=textwrap.dedent('''\
                                Path and file name of optional G2Module.ini to use.

                                '''))

    szgo_parser.add_argument('-ap', '--apiHostPort', type=int, default=docker_containers['restapi']['hostport'],
                             nargs=1, metavar='PORT',
                             help=textwrap.dedent('''\
                                Port number of the REST API server, default=%(default)s

                                '''))

    szgo_parser.add_argument('-wp', '--webAppHostPort', type=int, default=docker_containers['webapp']['hostport'],
                             nargs=1, metavar='PORT',
                             help=textwrap.dedent('''\
                                Port number of the Search Web App demo, default=%(default)s

                                '''))

    szgo_parser.add_argument('-sp', '--swaggerHostPort', type=int, default=docker_containers['swagger']['hostport'],
                             nargs=1, metavar='PORT',
                             help=textwrap.dedent('''\
                                Port number of Swagger UI, default=%(default)s
                                
                                '''))

    szgo_parser.add_argument('-nwa', '--noWebApp', default=False, action='store_true',
                             help=textwrap.dedent('''\
                                Don\'t deploy the Search Web App demo
                                
                                '''))

    szgo_parser.add_argument('-nsw', '--noSwagger', default=False, action='store_true',
                             help=textwrap.dedent('''\
                                Don\'t deploy the Swagger UI
                                
                                '''))

    stop_group = szgo_parser.add_mutually_exclusive_group()
    stop_group.add_argument('-s', '--contStop', default=False, action='store_true',
                            help=textwrap.dedent(f'''\
                                Stop any Docker containers named *{senzing_proj_name}
                                
                                '''))

    stop_group.add_argument('-r', '--contRemove', default=False, action='store_true',
                            help=textwrap.dedent(f'''\
                                Stop and remove any Docker containers named *{senzing_proj_name}
                                
                                '''))

    stop_group.add_argument('-rn', '--contRemoveNoPrompt', default=False, action='store_true',
                            help=textwrap.dedent(f'''\
                                Stop and remove any Docker containers named *{senzing_proj_name} without prompting
                                
                                '''))

    szgo_parser.add_argument('-i', '--info', default=False, action='store_true',
                             help=textwrap.dedent('''\
                                Display info for running containers for this project
                                
                                '''))

    szgo_parser.add_argument('-l', '--logs', type=str, const='SzGo', nargs='?', metavar='STRING',
                             help=textwrap.dedent('''\
                                Display logs for running container(s), use partial string to match multiple containers, default=%(const)s
                                
                                '''))

    # Use Suppress to not have in namespace unless specified
    szgo_parser.add_argument('-si', '--saveImages', default=argparse.SUPPRESS, nargs='*', metavar='IMAGE',
                             help=textwrap.dedent(f'''\
                                Save {SCRIPT_STEM} Docker images for loading on another machine, e.g. air gapped systems
                                
                                Unless instructed by Senzing support no arguments are required.
                                
                                '''))

    szgo_parser.add_argument('-sip', '--saveImagesPath', default=SENZING_VAR_PATH, nargs=1, metavar='PATH',
                             help=textwrap.dedent('''\
                                Path for saving a Docker images package to, default=%(default)s
                                
                                '''))

    szgo_parser.add_argument('-li', '--loadImages', type=str, nargs=1, metavar='FILE',
                             help=textwrap.dedent(f'''\
                                File to load {SCRIPT_STEM} Docker images from to this machine, e.g. air gapped systems
                                
                                '''))

    szgo_parser.add_argument('-aa', '--apiAdmin', default=False, action='store_true',
                             help=textwrap.dedent('''\
                                Enable admin mode on the API Server
                                
                                '''))

    szgo_parser.add_argument('-n', '--dockNet', type=str, default='szgo-network', nargs='?', metavar='NAME',
                             help=textwrap.dedent('''\
                                Name of a Docker network to create or use, default=%(default)s

                                '''))

    szgo_parser.add_argument('-ho', '--host', type=str, default=host_name, nargs='?',
                             help=textwrap.dedent('''\
                                Hostname or IP address, only use if tool can\'t determine correctly, default=%(default)s

                                '''))

    szgo_parser.add_argument('-ps', '--projectSuffix', type=str, default=None, nargs=1, metavar='SUFFIX',
                             help=textwrap.dedent(f'''\
                                Suffix to use for container names, default=%(default)s

                                '''))

    szgo_parser.add_argument('-db2c', '--db2CliPath', default=None, nargs=1,
                             help=textwrap.dedent('''\
                                Path to Db2 client CLI driver when using a Db2 database as the Senzing repository
                                
                                '''))

    # Undocumented args - advanced usage with guidance from Senzing support
    szgo_parser.add_argument('-il', '--imagesList', default=False, action='store_true', help=argparse.SUPPRESS)
    szgo_parser.add_argument('-ac', '--apiServerCommand', type=str, default=None, help=argparse.SUPPRESS, nargs=1, )
    szgo_parser.add_argument('-at', '--apiTag', type=str, default=None, help=argparse.SUPPRESS, nargs='?')
    szgo_parser.add_argument('-wt', '--webAppTag', type=str, default=None, help=argparse.SUPPRESS, nargs='?')
    szgo_parser.add_argument('-st', '--swaggerTag', type=str, default=None, help=argparse.SUPPRESS, nargs='?')
    szgo_parser.add_argument('-ij', '--iniToJson', default=False, action='store_true', help=argparse.SUPPRESS)
    szgo_parser.add_argument('-ijp', '--iniToJsonPretty', default=False, action='store_true', help=argparse.SUPPRESS)

    args = szgo_parser.parse_args()

    host_name = args.host

    # Import G2Paths after the get_senzing_root() check. G2Paths checks for SENZING_ROOT and exits if not set
    import G2Paths
    ini_file_name = pathlib.Path(G2Paths.get_G2Module_ini_path()) if not args.iniFile else pathlib.Path(
        args.iniFile[0]).resolve()
    G2Paths.check_file_exists_and_readable(ini_file_name)

    # Check ini file isn't using localhost for connection strings which won't work from within container
    ini_localhost_check(ini_file_name)

    # Convert G2Module.ini to JSON to pass to container
    ini_json = convert_ini2json(ini_file_name)

    # Convert INI to JSON, useful for using own REST API command
    if args.iniToJson or args.iniToJsonPretty:
        if args.iniToJson:
            print(ini_json)
        if args.iniToJsonPretty:
            print(json.dumps(ini_json, indent=4))
        sys.exit(0)

    # Check Docker Docker is installed, sudo access?
    docker_checks(SCRIPT_NAME)
    docker_client = docker_init()

    # Create Docker network if it doesn't exist
    if not args.contStop or not args.contRemove or not args.contRemoveNoPrompt or not args.info \
            or not args.logs or not args.saveImages or not args.loadImages or not args.imagesList:
        docker_net(docker_client, args.dockNet)

    # Set correct container names and project name if projectSuffix is used
    if args.projectSuffix:
        docker_containers['restapi']['containername'] = f'SzGo-API-{args.projectSuffix[0]}'
        docker_containers['webapp']['containername'] = f'SzGo-WEB-{args.projectSuffix[0]}'
        docker_containers['swagger']['containername'] = f'SzGo-Swagger-{args.projectSuffix[0]}'
        senzing_proj_name = args.projectSuffix if isinstance(args.projectSuffix, str) else args.projectSuffix[0]

    # Do clean up instead of deployment
    if args.contStop or args.contRemove or args.contRemoveNoPrompt:
        containers_stop_remove(senzing_proj_name, docker_client, docker_containers, args.contRemove,
                               args.contRemoveNoPrompt, args.dockNet)
        sys.exit(0)

    # Always stop and remove any existing containers if not performing a non-deploy option
    # Different args could be used between runs, want them to take effect with a new container instance
    if not hasattr(args,
                   'saveImages') and not args.loadImages and not args.info and not args.logs and not args.imagesList:
        containers_stop_remove(senzing_proj_name, docker_client, docker_containers, args.contRemove,
                               args.contRemoveNoPrompt, args.dockNet, startup_remove=True)

    # In deploying mode?
    if args.loadImages:
        load_images(docker_client, SENZING_VAR_PATH, args.loadImages[0])
        sys.exit(0)

    # Show currently running container details and exit
    if args.info:
        containers_info(docker_client, docker_containers, senzing_proj_name, host_name)

    # Show logs for a container, or set of containers if partial name string is supplied
    if args.logs:
        container_logs(docker_client, args.logs)

    # Warn about mismatching versions of images when manually specifying a tag
    if args.apiTag or args.webAppTag or args.swaggerTag:
        print(
            f'\n{Colors.WARN}WARNING:{Colors.COLEND} Use with caution, unmatched image versions may cause incompatibilities and errors!\n')
        sleep(5)

    # Check can reach net and access destinations of required resources?
    print('Checking for internet access and Senzing resources...', flush=True)
    access_versions = internet_access(DOCKER_LATEST_URL)
    access_dockerhub = internet_access(DOCKERHUB_URL)
    if args.imagesList:
        access_imagesList = internet_access(DOCKER_IMAGE_NAMES)
    print('\n')

    # Try and fetch the latest docker image versions
    versions = parse_versions(DOCKER_LATEST_URL) if access_versions else {}

    # Add the current pinned version numbers from DOCKER_LATEST_URL to the dictionary if available, else use latest
    docker_containers['restapi']['tag'] = versions[
        docker_containers['restapi']['latestsuffix']] if versions else 'latest'
    docker_containers['webapp']['tag'] = versions[docker_containers['webapp']['latestsuffix']] if versions else 'latest'
    docker_containers['swagger']['tag'] = versions[
        docker_containers['swagger']['latestsuffix']] if versions else 'latest'

    # Package images to use on another system
    if hasattr(args, 'saveImages'):
        save_images(docker_client, docker_containers, args.saveImages, args.saveImagesPath, access_dockerhub,
                    args.noWebApp, args.noSwagger, senzing_proj_name)
        sys.exit(0)

    # List images found on Senzing github
    if args.imagesList:
        list_image_names(DOCKER_IMAGE_NAMES, access_imagesList, versions)
        sys.exit(0)

    # Check if images exist already, add to dictionary for reference
    avail_images = []

    # Return list of repo names/tags, each could be tagged >1 and contain a list with >1 entries
    for i_list in [i.tags for i in docker_client.images.list()]:
        for image in i_list:
            avail_images.append(image.split(':')[0])

    docker_containers['restapi']['imageavailable'] = True if docker_containers['restapi'][
                                                                 'imagename'] in avail_images else False
    docker_containers['webapp']['imageavailable'] = True if docker_containers['webapp'][
                                                                'imagename'] in avail_images else False
    docker_containers['swagger']['imageavailable'] = True if docker_containers['swagger'][
                                                                 'imagename'] in avail_images else False

    # If can reach Docker Hub always try and pull images, otherwise detect if might be able to continue with installed local assets
    if access_dockerhub:
        pull_default_images(docker_client, docker_containers, args.noWebApp, args.noSwagger)
    else:
        print(textwrap.dedent(f'''\n\
            {Colors.WARN}WARNING:{Colors.COLEND} Cannot reach Senzing resources on the net, checking for available images...
        '''))

        # Need at minimum the rest api container!
        if not docker_containers['restapi']['imageavailable']:
            print(
                f'\n{Colors.ERROR}ERROR:{Colors.COLEND} Can\'t continue, can\'t access Docker Hub and no existing image for the REST API server is available\n')
            package_msg()
            sys.exit(1)
        else:
            print(
                f'\n{Colors.BLUE}INFO:{Colors.COLEND} Cannot access Docker Hub but a REST API server image is available to use (minimum requirement)...')

            # Find the newest tag for each available image and change the docker_containers['restapi']['tag'] for each image
            for k in docker_containers.keys():
                # Only need to do this if an image is available
                if docker_containers[k]["imageavailable"]:
                    images = docker_client.images.list(name=docker_containers[k]["imagename"])

                    images_to_sort = []
                    for image in images:
                        # If there is > 1 images found remove latest to find the true 'latest' version and don't rely on the meaningless latest tag
                        if len(images) > 1 and 'latest' in image.attrs["RepoTags"][0]:
                            continue
                        images_to_sort.append(image.attrs["RepoTags"][0])

                    images_to_sort.sort(reverse=True)
                    _, tag = images_to_sort[0].split(':')

                    docker_containers[k]['tag'] = tag

    # If tags requested in CLI args override any previously discovered tags
    if args.apiTag:
        docker_containers['restapi']['tag'] = args.apiTag
    if args.webAppTag:
        docker_containers['webapp']['tag'] = args.webAppTag
    if args.swaggerTag:
        docker_containers['swagger']['tag'] = args.swaggerTag

    # Fix ini parms for mounting inside container, when db type is sqlite also perform cluster checks and return an additional
    # mount to use to mount the sqlite file(s) into the container.
    db_type, ini_json_patched, sqlite_mount = patch_ini_json(ini_json)

    # Perform checks needed for mysql
    if db_type.lower() == 'mysql':
        mysql_check(SENZING_ROOT, LIB_MY_SQL, db_type, SENZING_SUPPORT)

    # Perform checks needed for Db2
    if db_type.lower() == 'db2':
        db2_check(args, SENZING_SUPPORT)

    if db_type == 'mssql':
        print('\nERROR: MSSQL databases are not supported currently')
        sys.exit(1)

    # Write INI parms to file, could use init-json string but less secure
    # Writing to file inside the project allows only those authorised to use project to see connection string
    ini_json_file = str(ini_file_name) + '_SzGo.json'
    with open(pathlib.Path(ini_json_file), 'w') as f:
        json.dump(ini_json_patched, f)

    # If running with sudo - for Docker - chown the file to the user after sudo creates it. This prevents permissions
    # errors if a user starts with sudo then no longer needs sudo to run docker, e.g. was added to docker group
    # Try to change to same uid and gid, if fails ignore gid
    if os.geteuid == 0:
        try:
            uid = os.getlogin()
            os.chown(ini_json_file, uid, uid)
        except Exception:
            with suppress(Exception):
                os.chown(ini_json_file, uid, -1)

    # REST Server - this is the minimum container to start, can be started without others
    api_host_port = args.apiHostPort[0] if isinstance(args.apiHostPort, list) else args.apiHostPort

    # Base volumes to mount in the container
    api_volumes = {f'{SENZING_ROOT}': {'bind': '/opt/senzing/g2', 'mode': 'rw'},
                   f'{SENZING_ROOT}/data': {'bind': '/opt/senzing/data', 'mode': 'rw'},
                   f'{SENZING_ROOT}/etc': {'bind': '/etc/opt/senzing', 'mode': 'rw'},
                   }

    # If db type is sqlite add extra mount for sqlite file(s) into container
    if sqlite_mount:
        api_volumes[sqlite_mount[0]] = sqlite_mount[1]

    # If db2 type is Db2 add extra mount for the required CLI drivers
    if db_type == 'db2':
        api_volumes[args.db2CliPath[0]] = {'bind': '/opt/IBM/db2/clidriver', 'mode': 'rw'}

    disp_pack_msg = False

    docker_run(docker_client,
               docker_containers,
               # Docker module docs say can pass a list, doesn't work. Entrypoint for image already specifies the jar to launch
               command=f'--enable-admin {"true" if args.apiAdmin else "false"} \
                         --allowed-origins * \
                         --concurrency 10 \
                         --read-only false \
                         --verbose true \
                         --http-port 8250 \
                         --bind-addr all \
                         --init-file /etc/opt/senzing/{ini_file_name.name + "_SzGo.json"}' if not args.apiServerCommand else
               args.apiServerCommand[0],
               container='restapi',
               detach=True,
               # Set hostname for use by the web app env var SENZING_API_SERVER_URL
               hostname=docker_containers['restapi']['containername'],
               image=docker_containers['restapi']['imagename'] + ':' + docker_containers['restapi']['tag'],
               name=docker_containers['restapi']['containername'],
               network=args.dockNet,
               # Order is: cont: host
               ports={docker_containers['restapi']['containerport']: api_host_port},
               remove=False,
               tty=True,
               # Get the ID of the user using USER, this ensures the correct uid if starting as sudo --preserve-env
               # The container uses this uid for files such as G2C.db and write operations
               user=f'{pwd.getpwnam(os.getenv("USER")).pw_uid}',
               volumes=api_volumes
               )

    # Try and get the API specification for Swagger, acts as test if it's up correctly too
    print('\n\n\tFetching API specification from REST server', end='')
    api_spec = get_api_spec(f'http://{host_name}:{api_host_port}/{SZGO_REST_SPEC}')
    print()

    # Dump the specification as JSON for Swagger from the rest server
    with open(f'{SENZING_ROOT}/var/{SZGO_REST_JSON}', 'w') as spec_file:
        # Only want the data section from the response - not the metadata
        json.dump(json.loads(api_spec)['data'], spec_file)

    # Web App
    web_app_host_port = args.webAppHostPort[0] if isinstance(args.webAppHostPort, list) else args.webAppHostPort

    if not args.noWebApp and docker_containers['webapp']['imageavailable']:

        docker_run(docker_client,
                   docker_containers,
                   container='webapp',
                   detach=True,
                   # Use Docker name of the container as the hostname - as per "docker inspect szgo-network"
                   # Can't rely on the hostname reported by the OS here. This host name is used inside the
                   # container and if the host name is localhost the entity search app tries to find the API
                   # Server within itself
                   environment=[
                       f'SENZING_API_SERVER_URL=http://{docker_containers["restapi"]["containername"]}:{docker_containers["restapi"]["containerport"]}',
                       'SENZING_WEB_SERVER_PORT=8081'
                   ],
                   image=docker_containers['webapp']['imagename'] + ':' + docker_containers['webapp']['tag'],
                   name=docker_containers['webapp']['containername'],
                   network=args.dockNet,
                   ports={docker_containers['webapp']['containerport']: web_app_host_port},
                   remove=False,
                   tty=True,
                   )
    else:
        if not args.noWebApp:
            print(
                f'\n{Colors.WARN}WARNING:{Colors.COLEND} Can\'t access web resources and no existing Web App Docker image exists, can\'t start Web App container.')
            disp_pack_msg = True

    # Swagger
    swagger_host_port = args.swaggerHostPort[0] if isinstance(args.swaggerHostPort, list) else args.swaggerHostPort

    if not args.noSwagger and docker_containers['swagger']['imageavailable']:

        docker_run(docker_client,
                   docker_containers,
                   container='swagger',
                   detach=True,
                   environment=[f'SWAGGER_JSON=/var/tmp/{SZGO_REST_JSON}'],
                   image=docker_containers['swagger']['imagename'] + ':' + docker_containers['swagger']['tag'],
                   name=docker_containers['swagger']['containername'],
                   network=args.dockNet,
                   ports={docker_containers['swagger']['containerport']: swagger_host_port},
                   remove=False,
                   tty=True,
                   volumes={
                       f'{SENZING_VAR_PATH}/{SZGO_REST_JSON}': {'bind': f'/var/tmp/{SZGO_REST_JSON}', 'mode': 'ro'}}
                   )

    else:
        if not args.noSwagger:
            print(
                f'\n{Colors.WARN}WARNING:{Colors.COLEND} Can\'t access web resources and no existing Swagger Docker image exists, can\'t start Swagger container.')
            disp_pack_msg = True

    if disp_pack_msg:
        package_msg()

    api_server_url = f'http://{host_name}:{api_host_port}'
    entity_search_url = f'http://{host_name}:{web_app_host_port}' if not args.noWebApp and docker_containers['webapp'][
        'startedok'] else '--noWebApp (-nwa) used or an error occurred'
    swagger_url = f'http://{host_name}:{swagger_host_port}' if not args.noSwagger and docker_containers['swagger'][
        'startedok'] else '--noSwagger (-nsw) used or an error occurred'

    print(textwrap.dedent(f'''\n\n\
        {Colors.BLUE}{Colors.BOLD}Resources
        ---------{Colors.COLEND}
        
        REST API Server: {api_server_url}
        Web App demo:    {entity_search_url}
        Swagger GUI:     {swagger_url}
        
        Help: {SZGO_HELP}
            '''))


if __name__ == '__main__':
    main()
