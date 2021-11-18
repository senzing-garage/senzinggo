 SenzingGo

## Overview

The SenzingGo utility provides rapid deployment of the following Docker containers on a bare metal Linux installation of the Senzing APIs:
- [Senzing REST API Server](https://github.com/Senzing/senzing-api-server)
- [Senzing Entity Search App (sample demo application)](https://github.com/Senzing/entity-search-web-app)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)

SenzingGo is intended to be easy to use and deploy resources quickly to aid in getting started with the Senzing APIs; without requiring Docker skills. Due to its rapid deployment and ease of use, it is targetted at testing, development and education. 

SenzingGo is not intended for production use, it does not provide authentication or secure transport of communications. Such topics are outside the intended use and scope of SenzingGo.

### Contents

blah blah ANT

### Legend
1. :thinking: - A "thinker" icon means that a little extra thinking may be required.
   Perhaps you'll need to make some choices.
   Perhaps it's an optional step.
1. :pencil2: - A "pencil" icon means that the instructions may need modification before performing.
1. :warning: - A "warning" icon means that something tricky is happening, so pay attention.

### Prerequisites

- Supported Linux operating system
- Senzing APIs installation
- Creation of a Senzing project (see above link)
- Docker
- Python Docker module

    ```console
    pip3 install docker
    ```
- sudo access or user added to the Linux docker group
  - SenzingGo executes API calls against Docker and privelges to use it are required

:warning: Recent versions of Red Hat systems use Podman in place of Docker. Podman is not currently supported, see the Docker link above for installation of Docker if you don't rely on Podman.

### Installation

SenzingGo will be included in V3 of the Senzing APIs. In the meantime:
1. Download SenzingGo.py and place it in the python directory of your Senzing API project
2. Add execute permission to SenzingGo.py
    ```console
    cd <project_path>/python
    chmod +x SenzingGo.py
    ```

4. As usual, ensure you have sourced the setupEnv file for your Senzing API project to set the Senzing environment

    ```console
    source <project_path>/setupEnv
    ```

### Usage Overview

```console
 usage: SenzingGo.py [-h] [-c INIFILE] [-ap PORT] [-wp PORT] [-sp PORT] [-nwa] [-nsw] [-s | -r | -rn] [-i] [-l [STRING]] [-si [IMAGE [IMAGE ...]]] [-sip PATH] [-li FILE] [-aa] [-n [NAME]] [-ho [HOST]]
                    [-ps SUFFIX] [-db2c DB2CLIPATH]

Utility to rapidly deploy Docker containers for REST API server, Entity Search App and Swagger UI

Additional information: https://github.com/Senzing/senzinggo

optional arguments:
  -h, --help            show this help message and exit
  -c INIFILE, --iniFile INIFILE
                        Path and file name of optional G2Module.ini to use.
                        
  -ap PORT, --apiHostPort PORT
                        Port number of the REST API server, default=8250
                        
  -wp PORT, --webAppHostPort PORT
                        Port number of the Search Web App demo, default=8251
                        
  -sp PORT, --swaggerHostPort PORT
                        Port number of Swagger UI, default=9180
                        
  -nwa, --noWebApp      Don't deploy the Search Web App demo
                        
  -nsw, --noSwagger     Don't deploy the Swagger UI
                        
  -s, --contStop        Stop any Docker containers named *2_8_3-Release
                        
  -r, --contRemove      Stop and remove any Docker containers named *2_8_3-Release
                        
  -rn, --contRemoveNoPrompt
                        Stop and remove any Docker containers named *2_8_3-Release without prompting
                        
  -i, --info            Display info for running containers for this project
                        
  -l [STRING], --logs [STRING]
                        Display logs for running container(s), use partial string to match multiple containers, default=SzGo
                        
  -si [IMAGE [IMAGE ...]], --saveImages [IMAGE [IMAGE ...]]
                        Save SenzingGo Docker images for loading on another machine, e.g. air gapped systems
                        
                        Unless instructed by Senzing support no arguments are required.
                        
  -sip PATH, --saveImagesPath PATH
                        Path for saving a Docker images package to, default=/home/ant/senzprojs/2_8_3-Release/var
                        
  -li FILE, --loadImages FILE
                        File to load SenzingGo Docker images from to this machine, e.g. air gapped systems
                        
  -aa, --apiAdmin       Enable admin mode on the API Server
                        
  -n [NAME], --dockNet [NAME]
                        Name of a Docker network to create or use, default=szgo-network
                        
  -ho [HOST], --host [HOST]
                        Hostname or IP address, only use if tool can't determine correctly, default=ant76
                        
  -ps SUFFIX, --projectSuffix SUFFIX
                        Suffix to use for container names, default=2_8_3-Release
                        
  -db2c DB2CLIPATH, --db2CliPath DB2CLIPATH
                        Path to Db2 client CLI driver when using a Db2 database as the Senzing repository

```

### Usage

Although SenzingGo has many arguments, it is executed in it's simplest form with no arguments. 

```
./SenzingGo.py
```

Upon execution the script will:

1. Perform checks to ensure Docker is installed and the current user has privileges to execute Docker commands
2. Check for the latest versions of Docker images utilized
3. Pull the required Docker images (if not already locally available)
4. Run the Docker images and instantiate running containers for the previously described assets
