# Copyright 2020 Spotify AB

import logging
import os

import docker

from klio_cli.utils import docker_utils


class BaseDockerizedPipeline(object):
    ENTRYPOINT = "klioexec"
    GCP_CRED_FILE = "gcloud/application_default_credentials.json"
    HOST_GCP_CRED_PATH = os.path.join(".config", GCP_CRED_FILE)
    CONTAINER_GCP_CRED_PATH = os.path.join("/usr", GCP_CRED_FILE)
    CONTAINER_JOB_DIR = "/usr/src/app"
    DOCKER_LOGGER_NAME = "klio.base_docker_pipeline"

    def __init__(self, job_dir, klio_config, docker_runtime_config):
        self.job_dir = job_dir
        # TODO: this should be KlioConfig object
        self.klio_config = klio_config
        self.docker_runtime_config = docker_runtime_config
        self._docker_client = None
        self._docker_logger = self._get_docker_logger()

    @property
    def _full_image_name(self):
        return "{}:{}".format(
            self.klio_config.pipeline_options.worker_harness_container_image,
            self.docker_runtime_config.image_tag,
        )

    def _get_docker_logger(self):
        # create a separate logger for specific run output
        # to avoid the `INFO:root` prefix
        logger = logging.getLogger(self.DOCKER_LOGGER_NAME)
        formatter = logging.Formatter("%(message)s")
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        console.setLevel(logging.INFO)
        logger.addHandler(console)

        # prevent from propagating to root logger & logging duplicate msgs
        logger.propagate = False
        return logger

    def _run_docker_container(self, runflags):
        container = self._docker_client.containers.run(**runflags)

        # TODO: container.logs(stream=True) redirects stderr to stdout.
        #       We should use appropriate streams so it's obvious to the use.
        #       (@jpvelez)
        for line in container.logs(stream=True):
            self._docker_logger.info(line.decode("utf-8").strip("\n"))

        exit_status = container.wait()
        return exit_status["StatusCode"]

    def _get_environment(self):
        cred_path = BaseDockerizedPipeline.CONTAINER_GCP_CRED_PATH
        return {
            "PYTHONPATH": BaseDockerizedPipeline.CONTAINER_JOB_DIR,
            "GOOGLE_APPLICATION_CREDENTIALS": cred_path,
            "USER": os.environ.get("USER"),
        }

    def _get_volumes(self):
        host_cred_path = os.path.join(
            os.environ.get("HOME"), BaseDockerizedPipeline.HOST_GCP_CRED_PATH
        )
        return {
            host_cred_path: {
                "bind": BaseDockerizedPipeline.CONTAINER_GCP_CRED_PATH,
                "mode": "rw",  # Fails if no write access
            },
            self.job_dir: {
                "bind": BaseDockerizedPipeline.CONTAINER_JOB_DIR,
                "mode": "rw",
            },
        }

    def _get_command(self, *args, **kwargs):
        raise NotImplementedError

    def _get_docker_runflags(self, *args, **kwargs):
        return {
            "image": self._full_image_name,
            # overwrite fnapi image entrypoint
            "entrypoint": self.ENTRYPOINT,
            "command": self._get_command(*args, **kwargs),
            # mount klio code
            "volumes": self._get_volumes(),
            "environment": self._get_environment(),
            # return container obj to stream logs
            "detach": True,
            # remove container when entrypoint exists
            "auto_remove": True,
        }

    def _setup_docker_image(self):
        image_exists = docker_utils.docker_image_exists(
            self._full_image_name, self._docker_client
        )

        if not image_exists or self.docker_runtime_config.force_build:
            logging.info("Building worker image: %s" % self._full_image_name)

            _pipe_opts = self.klio_config.pipeline_options
            return docker_utils.build_docker_image(
                self.job_dir,
                _pipe_opts.worker_harness_container_image,
                self.docker_runtime_config.image_tag,
                self.docker_runtime_config.config_file_override,
            )

        logging.info("Found worker image: %s" % self._full_image_name)

    def _check_docker_setup(self):
        self._docker_client = docker.from_env()
        docker_utils.check_docker_connection(self._docker_client)
        docker_utils.check_dockerfile_present(self.job_dir)

    def _check_gcp_credentials_exist(self):
        host_cred_path = os.path.join(
            os.environ.get("HOME"), BaseDockerizedPipeline.HOST_GCP_CRED_PATH
        )
        if not os.path.isfile(host_cred_path):
            logging.warning(
                "Could not read gcloud credentials at {}, which may cause"
                "your job to fail to run if it uses GCP resources. "
                "Try running `gcloud auth application-default login`"
                ". See here for more information: https://cloud.google.com/"
                "sdk/gcloud/reference/auth/application-default/login".format(
                    host_cred_path
                )
            )

    def run(self, *args, **kwargs):
        # bail early
        self._check_gcp_credentials_exist()
        self._check_docker_setup()

        self._setup_docker_image()
        runflags = self._get_docker_runflags(*args, **kwargs)

        exit_code = self._run_docker_container(runflags)
        return exit_code