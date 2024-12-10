## Instructions for set-up
1. Clone this repository:
```
git clone https://github.com/IDinsight/experiments-engine.git
```

2. Make environment files
Navigate to `deployment/docker-compose`. Copy the template `.env` files to create a `.base.env` and `.backend.env` files

3. Set-up a conda environment
Navigate to the root of this repository and run `make fresh-env`

4. Set-up databases
From the root of the repository run `make setup-db && make setup-redis`

5. Add admin-users to the DB
From the root of the repository run `ptyhon backend/add_users_to_db.py`. The default admin credentials are defined in the `add_users_to_db.py` file.

6. Install required frontend packages
Navigate to `frontend` and run `npm install`.

7. Spin up the app
From the root of the repository run `python backend/main.py`.
Then navigate to `frontend` and run `npm run dev`

8. Explore!
Log in with the admin credentials and experiment :)
