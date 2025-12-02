#### Document assumes Docker is installed on the Desktop and user is familiar with Docker commands
#### This document explains minimal effort to test neo4j without actually installing anything on your laptop through Docker container approach. Don't use the command literally.  Some place you have to substitute your own strings like NEO4J_HOME or password etc.

#### Documentation through Docker Approach

#### Reference: https://neo4j.com/docs/operations-manual/current/docker/

#### export NEO4J_HOME=/Users/<username>/DevOps/Neo4JDev/Virtual/

For persistant data use Docker Volumes

1. mkdir $NEO4J_HOME/import   #Make csv and other importable files available to neo4j-admin import.
2. mkdir $NEO4J_HOME/data     #The data store for the Neo4j database. See Mounting storage to /data
3. mkdir $NEO4J_HOME/logs     #Output directory for Neo4j logs. See Mounting storage to /logs.
4. mkdir $NEO4J_HOME/plugins  #Allows you to install plugins in containerized Neo4j.
5. mkdir $NEO4J_HOME/conf     #Pass configuration files to Neo4j on startup.

```
docker run --name neo4j-docker \
           --publish=7474:7474 --publish=7473:7473 --publish=7687:7687 \
           --env NEO4J_AUTH=neo4j/<useapa44word-changem> \
           --env NEO4J_PLUGINS='["apoc", "bloom", "graph-data-science", "genai"]' \
           --volume=$NEO4J_HOME/data:/data \
           --volume=$NEO4J_HOME/plugins:/plugins \
           --volume=$NEO4J_HOME/logs:/logs \
           --volume=$NEO4J_HOME/import:/import \
           neo4j:2025.10.1
```

Variation of docker run (Use docker run -it --rm for interactive sessions or docker run --detatch )


Using docker-compose.yml file

```
services:
  neo4j:
    image: neo4j:2025.10.1
    volumes:
        - /$HOME/DevOps/Neo4JDev/Virtual/logs:/logs
        - /$HOME/DevOps/Neo4JDev/Virtual/data:/data
        - /$HOME/DevOps/Neo4JDev/Virtual/plugins:/plugins
        - /$HOME/DevOps/Neo4JDev/Virtual/import:/import
    environment:
        - NEO4J_AUTH=neo4j/<useapa44word-changem>
        - NEO4J_PLUGINS=["apoc", "bloom", "graph-data-science", "genai"]
    ports:
      - "7474:7474"
      - "7473:7473"
      - "7687:7687"

```

docker-compose up -d # to start the container
docker-compose down  # to stop the container


Browser Access at : http://localhost:7474/
username: neo4j
password: useapa44word-changem
