# Multi-pod docker-compose deployments

This is a deployment of a multi-container service to demonstrate Docker capabilities. Docker internally 
uses round-robin to evenly distribute requests among every container.

In this example, we are exposing two services of the same Docker image, which is a very simple FastAPI web app. 
Each service has two replicas. The two services are publicly exposed using an NGINX reverse proxy.

Additionally, each replica exposes a dedicated port for the /metrics endpoint, which is used by Prometheus to collect metrics.

## Tutorial

This is the definition of the FastAPI service. Docker will randomly assign a port between the range of 9101 and 9200 to each replica.

```
app-group-1:
    build: .
    deploy:
        replicas: 2
        restart_policy:
            condition: on-failure
    ports:
        - "9101-9200:80" # expose prometheus metrics
```

This is the definition of the nginx service.

```
nginx:
    image: nginx:latest
    volumes:
        - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
        - app-group-1
        - app-group-2
    ports:
        - "80:80"
```

The Nginx reverse proxy configuration below is used to expose the service through group replicas. 

```
user  nginx;

events {
  worker_connections   1000;
}
http {
  server {
    listen 80;
    server_name app-group-1;
  
    location / {
      proxy_pass http://app-group-1;
    }
  }

  server {
    listen 80;
    server_name app-group-2;
  
    location / {
      proxy_pass http://app-group-2;
    }
  }
}
```

By using the internal name of the service, you can redirect the request to the corresponding group. The name should be identical to the service name mentioned in the docker-compose file. 

Docker then redirects the traffic to each replica using a round-robin distribution algorithm.

To test this, please add the following records to your local hosts file.

```
127.0.0.1 		app-group-1
127.0.0.1 		app-group-2
```

Then, call the `app-group-1` service using the following command.

```
curl -X 'GET' 'http://app-group-1/?example=test'
```

You expect to receive the following response. Consecutive calls must return different container IDs.

```
$ curl -X 'GET' 'http://app-group-1/?example=test'
"782bf3ef4322"
$ curl -X 'GET' 'http://app-group-1/?example=test'
"3c56bd588a50"
```

You are expecting the same behavior for the `app-group-2`.

```
curl -X 'GET' 'http://app-group-2/?example=test'
```

Using the following command, you can find the allocated port for every service replica.

```
$ docker compose ps
NAME                                      IMAGE                                   COMMAND                  SERVICE             CREATED             STATUS              PORTS
python-docker-multi-nodes-app-group-1-2   python-docker-multi-nodes-app-group-1   "uvicorn app.main:ap…"   app-group-1         10 hours ago        Up 27 minutes       0.0.0.0:9101->80/tcp
python-docker-multi-nodes-app-group-1-3   python-docker-multi-nodes-app-group-1   "uvicorn app.main:ap…"   app-group-1         6 minutes ago       Up 6 minutes        0.0.0.0:9102->80/tcp
python-docker-multi-nodes-app-group-2-1   python-docker-multi-nodes-app-group-2   "uvicorn app.main:ap…"   app-group-2         10 hours ago        Up 27 minutes       0.0.0.0:9090->80/tcp
python-docker-multi-nodes-app-group-2-2   python-docker-multi-nodes-app-group-2   "uvicorn app.main:ap…"   app-group-2         6 minutes ago       Up 6 minutes        0.0.0.0:9091->80/tcp
python-docker-multi-nodes-nginx-1         nginx:latest                            "/docker-entrypoint.…"   nginx               22 minutes ago      Up 6 minutes        0.0.0.0:80->80/tcp
```

Lastly, with the following, you can access the metrics of every replica.

```
$ curl -X 'GET' 'http://localhost:9101/metrics'
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 485.0
python_gc_objects_collected_total{generation="1"} 292.0
python_gc_objects_collected_total{generation="2"} 0.0
...
# HELP http_request_duration_seconds_created Latency with only few buckets by handler. Made to be only used if aggregation by handler is important.
# TYPE http_request_duration_seconds_created gauge
http_request_duration_seconds_created{handler="/",method="GET"} 1.68949676728942e+09
```

That's all, folks! This tutorial is finished!