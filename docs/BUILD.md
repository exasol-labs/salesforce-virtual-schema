# Building and Testing

1. Install requirements:

    ```shell
    python3 -m pip --user install -r requirements.txt
    ```

1. Run the build script:

    ```shell
   python3 ./build.py
    ```

If things went well, you will have

- SQL scripts in `sql/deploy/` that can be deployed on Exasol
- python scripts in `python/` that can be used for local testing (Actually, no. Work in progress)
