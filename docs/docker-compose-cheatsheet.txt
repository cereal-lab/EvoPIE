Bring the whole thing up
    docker-compose up -d --build

Check that everything is working
    docker-compose ps
    docker-compose logs
    docker-compose logs -f -t #follow logs live w/ timestamps

Bring the whole thing down
    docker-compose down -v
