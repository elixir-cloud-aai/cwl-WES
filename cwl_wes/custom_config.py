"""Custom app config models."""
import string
from typing import Dict, List, Optional
from foca.models.config import FOCABaseConfig


class StorageConfig(FOCABaseConfig):
    """Model for task run and storage configuration.

    Args:
        tmp_dir: Temporary run directory path
        permanent_dir: Permanent working directory path
        remote_storage_url: Remote file storage FTP endpoint

    Attributes:
        tmp_dir: Temporary run directory path
        permanent_dir: Permanent working directory path
        remote_storage_url: Remote file storage FTP endpoint

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> StorageConfig(
        ...     tmp_dir='/data/tmp',
        ...     permanent_dir='/data/output',
        ...     remote_storage_url='ftp://ftp.private/upload'
        ... )
        StorageConfig(tmp_dir='/data/tmp', permanent_dir='/data/output', remote_storage_url='ftp://ftp.private/upload')
    """

    permanent_dir: str = "/data/output"
    tmp_dir: str = "/data/tmp"
    remote_storage_url: str = "ftp://ftp-private.ebi.ac.uk/upload/foivos"


class CeleryConfig(FOCABaseConfig):
    """Model for celery configurations.

    Args:
        timeout: Celery task timeout.
        message_maxsize: Celery message max size.

    Attributes:
        timeout: Celery task timeout.
        message_maxsize: Celery message max size.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> CeleryConfig(
        ...     timeout=15,
        ...     message_maxsize=1024
        ... )
        CeleryConfig(timeout=15, message_maxsize=1024)
    """

    timeout: float = 0.1
    message_maxsize: int = 16777216


class WorkflowTypeVersionConfig(FOCABaseConfig):
    """Workflow type versions supported by this service.
    Args:
        workflow_type_version: List of one or more acceptable versions for the
            workflow type.

    Attributes:
        workflow_type_version: List of one or more acceptable versions for the
            workflow type.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> WorkflowTypeVersionConfig(
        ...     workflow_type_version=['v1.0']
        ... )
        WorkflowTypeVersionConfig(workflow_type_version=['v1.0'])
    """

    workflow_type_version: Optional[List[str]] = []


class DefaultWorkflowEngineParameterConfig(FOCABaseConfig):
    """Model for default workflow engine parameters.

    Args:
        name: Parameter name.
        type: Parameter type.
        default_value: Stringified version of default parameter.

    Attributes:
        name: Parameter name.
        type: Parameter type.
        default_value: Stringified version of default parameter.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> DefaultWorkflowEngineParameterConfig(
        ...     name='name',
        ...     type='str',
        ...     default_value='default'
        ... )
        DefaultWorkflowEngineParameterConfig(name='name', type='str', default_value='default')
    """

    name: Optional[str]
    type: Optional[str]
    default_value: Optional[str]


class TagsConfig(FOCABaseConfig):
    """Model for service info tag configuration.

    Args:
        known_tes_endpoints: Valid TES endpoints.

    Attributes:
        known_tes_endpoints: Valid TES endpoints.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> TagsConfig(
        ...     known_tes_endpoints='https://tes.endpoint',
        ... )
        TagsConfig(known_tes_endpoints='https://tes.endpoint')
    """

    known_tes_endpoints: str = "https://tes.tsi.ebi.ac.uk/|https://tes-dev.tsi.ebi.ac.uk/|https://csc-tesk.c03.k8s-popup.csc.fi/|https://tesk.c01.k8s-popup.csc.fi/"


class ServiceInfoConfig(FOCABaseConfig):
    """Model for service info configurations.

    Args:
        contact_info: Email address/webpage URL with contact information.
        auth_instructions_url: Web page URL with information about how to get an
          authorization token necessary to use a specific endpoint.
        supported_filesystem_protocols: Filesystem protocols supported by this
            service.
        supported_wes_versions: Version(s) of the WES schema supported by this
            service.
        workflow_type_versions: Map with keys as the workflow format type name and
            value is a `WorkflowTypeVersionConfig` object which simply contains an
            array of one or more version strings.
        workflow_engine_versions: Workflow engine(s) used by this WES service.
        default_workflow_engine_parameters: Each workflow engine can present additional
            parameters that can be sent to the workflow engine.
        tags: A key-value map of arbitrary, extended metadata outside the scope of the above but
            useful to report back.

    Attributes:
        contact_info: Email address/webpage URL with contact information.
        auth_instructions_url: Web page URL with information about how to get an
          authorization token necessary to use a specific endpoint.
        supported_filesystem_protocols: Filesystem protocols supported by this
            service.
        supported_wes_versions: Version(s) of the WES schema supported by this
            service.
        workflow_type_versions: Map with keys as the workflow format type name and
            value is a `WorkflowTypeVersionConfig` object which simply contains an
            array of one or more version strings.
        workflow_engine_versions: Workflow engine(s) used by this WES service.
        default_workflow_engine_parameters: Each workflow engine can present additional
            parameters that can be sent to the workflow engine.
        tags: A key-value map of arbitrary, extended metadata outside the scope of the above but
            useful to report back.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> ServiceInfoConfig(
        ...     contact_info='https://contact.url',
        ...     auth_instructions_url='https://auth.url',
        ...     supported_filesystem_protocols=['ftp', 'https', 'local'],
        ...     supported_wes_versions=['1.0.0'],
        ...     workflow_type_versions={'CWL': WorkflowTypeVersionConfig(workflow_type_version=['v1.0'])},
        ...     workflow_engine_versions={},
        ...     default_workflow_engine_parameters=[],
        ...     tags=TagsConfig(known_tes_endpoints='https://tes.endpoint/')
        ... )
        ServiceInfoConfig(contact_info='https://github.com/elixir-cloud-aai/cwl-WES', auth_instruc\
        tions_url='https://www.elixir-europe.org/services/compute/aai', supported_filesystem_proto\
        cols=['ftp', 'https', 'local'], supported_wes_versions=['1.0.0'], workflow_type_versions={\
        'CWL': WorkflowTypeVersionConfig(workflow_type_version=['v1.0'])}, workflow_engine_version\
        s={}, default_workflow_engine_parameters=[], tags=TagsConfig(known_tes_endpoints='https://\
        tes.tsi.ebi.ac.uk/|https://tes-dev.tsi.ebi.ac.uk/|https://csc-tesk.c03.k8s-popup.csc.fi/|h\
        ttps://tesk.c01.k8s-popup.csc.fi/'))
    """

    contact_info: str = "https://github.com/elixir-cloud-aai/cwl-WES"
    auth_instructions_url: str = (
        "https://www.elixir-europe.org/services/compute/aai"
    )
    supported_filesystem_protocols: List[str] = ["ftp", "https", "local"]
    supported_wes_versions: List[str] = ["1.0.0"]
    workflow_type_versions: Dict[str, WorkflowTypeVersionConfig] = {
        "CWL": WorkflowTypeVersionConfig(workflow_type_version=["v1.0"]),
    }
    workflow_engine_versions: Dict[str, str] = {}
    default_workflow_engine_parameters: List[
        DefaultWorkflowEngineParameterConfig
    ] = []
    tags: TagsConfig = TagsConfig()


class TesServerConfig(FOCABaseConfig):
    """Model for tes server configuration.

    Args:
        url: TES Endpoint URL.
        timeout: Request time out.
        status_query_params: Request query parameters.

    Attributes:
        url: TES Endpoint URL.
        timeout: Request time out.
        status_query_params: Request query parameters.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> TesServerConfig(
        ...     url='https://tes.endpoint',
        ...     timeout=5,
        ...     status_query_params='FULL'
        ... )
        TesServerConfig(url='https://tes.endpoint', timeout=5, status_query_params='FULL')
    """

    url: str = "https://csc-tesk.c03.k8s-popup.csc.fi/"
    timeout: int = 5
    status_query_params: str = "FULL"


class DRSServerConfig(FOCABaseConfig):
    """Model for DRS server configuration.

    Args:
        port: Port for resolving DRS URIs;
            set to `null` to use default (443).
        base_path: Base path for resolving DRS URIs;
            set to `null` to use default (`ga4gh/drs/v1`).
        use_http: Use `http` for resolving DRS URIs;
            set to `False` to use default (`https`).
        file_types:  Extensions of files to scan for DRS URI resolution.

    Attributes:
        port: Port for resolving DRS URIs;
            set to `null` to use default (443).
        base_path: Base path for resolving DRS URIs;
            set to `null` to use default (`ga4gh/drs/v1`).
        use_http: Use `http` for resolving DRS URIs;
            set to `False` to use default (`https`).
        file_types:  Extensions of files to scan for DRS URI resolution.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> DRSServerConfig(
        ...     port=443,
        ...     base_path='ga4gh/drs/v1',
        ...     use_http=False,
        ...     file_types=['cwl', 'yaml', 'yml']
        ... )
        DRSServerConfig(port=443, base_path='ga4gh/drs/v1', use_http=False, file_types=['cwl', 'yaml', 'yml'])
    """

    port: Optional[int] = None
    base_path: Optional[str] = None
    use_http: bool = False
    file_types: List[str] = ["cwl", "yaml", "yml"]


class IdConfig(FOCABaseConfig):
    """Model for defining unique identifier for services on cloud registry.

    Args:
        charset: A string of allowed characters or an expression evaluating to
            a string of allowed characters.
        length: Length of returned string.

    Attributes:
        charset: A string of allowed characters or an expression evaluating to
            a string of allowed characters.
        length: Length of returned string.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> IdConfig(
        ...     charset='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        ...     length=6
        ... )
        IdConfig(charset='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', length=6)
    """

    length: int = 6
    charset: str = string.ascii_uppercase + string.digits


class ControllerConfig(FOCABaseConfig):
    """Model for controller configurations.

    Args:
        default_page_size: Pagination page size.
        timeout_cancel_run: Timeout for `cancel_run` workflow.
        timeout_run_workflow: Timeout for `run_workflow` workflow.
        tes_server: TES Server config parameters.
        drs_server: DRS Server config parameters.
        runs_id: Identifier config parameters.

    Attributes:
        default_page_size: Pagination page size.
        timeout_cancel_run: Timeout for `cancel_run` workflow.
        timeout_run_workflow: Timeout for `run_workflow` workflow.
        tes_server: TES Server config parameters.
        drs_server: DRS Server config parameters.
        runs_id: Identifier config parameters.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.

    Example:
        >>> ControllerConfig(
        ...     default_page_size=5,
        ...     timeout_cancel_run=60,
        ...     timeout_run_workflow=None
        ... )
        ControllerConfig(default_page_size=5, timeout_cancel_run=60, timeout_run_workflow=60)
    """

    default_page_size: int = 5
    timeout_cancel_run: int = 60
    timeout_run_workflow: Optional[int] = None
    tes_server: TesServerConfig = TesServerConfig()
    drs_server: DRSServerConfig = DRSServerConfig()
    runs_id: IdConfig = IdConfig()


class CustomConfig(FOCABaseConfig):
    """Model for custom configuration parameters.

    Args:
        storage: Storage config parameters.
        celery: Celery config parameters.
        controller: Controller config parameters.
        service_info: Service Info config parameters.

    Attributes:
        storage: Storage config parameters.
        celery: Celery config parameters.
        controller: Controller config parameters.
        service_info: Service Info config parameters.

    Raises:
        pydantic.ValidationError: The class was instantianted with an illegal
            data type.
    """

    storage: StorageConfig = StorageConfig()
    celery: CeleryConfig = CeleryConfig()
    controller: ControllerConfig = ControllerConfig()
    service_info: ServiceInfoConfig = ServiceInfoConfig()
