## Instructions for set-up
1. Clone this repository:
```
git clone https://github.com/IDinsight/experiments-engine.git
```

2. Make environment files
Navigate to `deployment/docker-compose`. Copy the template `.env` files to create a `.base.env` and `.backend.env` files

3. Set-up a conda environment
Navigate to the root of this repository and run `make fresh-env`

3. Run the app
From the root of the repository run `make run-backend`, and in a separate terminal session `make run-frontend`.

4. Explore!
Log in with the admin credentials and experiment :)
