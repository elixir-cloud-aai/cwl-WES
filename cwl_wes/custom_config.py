"""Custom app config models."""
import string
from typing import Dict, List, Optional
from foca.models.config import FOCABaseConfig

class StorageConfig(FOCABaseConfig):
    permanent_dir: str = '/data/output'
    tmp_dir: str = '/data/tmp'
    remote_storage_url: str = 'ftp://ftp-private.ebi.ac.uk/upload/foivos'


class MonitorConfig(FOCABaseConfig):
    timeout: float = 0.1


class CeleryConfig(FOCABaseConfig):
    monitor: MonitorConfig = MonitorConfig()
    message_maxsize: int = 16777216


class EndpointConfig(FOCABaseConfig):
    default_page_size: int = 5
    timeout_cancel_run: int = 60
    timeout_run_workflow: Optional[int] = None


class WorkflowTypeVersionConfig(FOCABaseConfig):
    """Workflow type versions supported by this service.
    Args:
        workflow_type_version: List of one or more acceptable versions for the
            workflow type.
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
    """
    name: Optional[str]
    type: Optional[str]
    default_value: Optional[str]


class TagsConfig(FOCABaseConfig):
    known_tes_endpoints: str = 'https://tes.tsi.ebi.ac.uk/|https://tes-dev.tsi.ebi.ac.uk/|https://csc-tesk.c03.k8s-popup.csc.fi/|https://tesk.c01.k8s-popup.csc.fi/'
    app_version: str = '0.15.0'


class ServiceInfoConfig(FOCABaseConfig):
    contact_info: str = 'https://github.com/elixir-cloud-aai/cwl-WES'
    auth_instructions_url: str = 'https://www.elixir-europe.org/services/compute/aai'
    supported_filesystem_protocols: List[str] = ['ftp', 'https', 'local']
    supported_wes_versions: List[str] = ['1.0.0']
    workflow_type_versions: Dict[str, WorkflowTypeVersionConfig] = {
        'CWL': WorkflowTypeVersionConfig(workflow_type_version=['v1.0']),
    }
    workflow_engine_versions: Dict[str, str] = {}
    default_workflow_engine_parameters: List[
        DefaultWorkflowEngineParameterConfig
    ] = []
    tags: TagsConfig = TagsConfig()


class TesServerConfig(FOCABaseConfig):
    url: str = 'https://csc-tesk.c03.k8s-popup.csc.fi/'
    timeout: int = 5
    status_query_params: str = 'FULL'


class DRSServerConfig(FOCABaseConfig):
    port: Optional[int] = None
    base_path: Optional[str] = None
    use_http: bool = False
    file_types: List[str] = ['cwl', 'yaml', 'yml']


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


class CustomConfig(FOCABaseConfig):
    storage: StorageConfig = StorageConfig()
    celery: CeleryConfig = CeleryConfig()
    endpoint_params: EndpointConfig = EndpointConfig()
    service_info: ServiceInfoConfig = ServiceInfoConfig()
    tes_server: TesServerConfig = TesServerConfig()
    drs_server: DRSServerConfig = DRSServerConfig()
    runs_id: IdConfig = IdConfig()
 