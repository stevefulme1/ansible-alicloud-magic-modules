# Alibaba Cloud Magic Modules

[![CI](https://github.com/stevefulme1/ansible-alicloud-magic-modules/actions/workflows/ci.yml/badge.svg)](https://github.com/stevefulme1/ansible-alicloud-magic-modules/actions/workflows/ci.yml)

Generate fully-functional [Ansible](https://www.ansible.com/) modules for Alibaba Cloud from declarative YAML resource definitions -- inspired by Google's [Magic Modules](https://github.com/GoogleCloudPlatform/magic-modules) for GCP/Terraform.

Instead of hand-writing hundreds of lines of boilerplate per Alibaba Cloud resource, you describe the resource once in YAML and the generator produces:

- A **CRUD module** (`alicloud_<resource>.py`) with `present`/`absent` state management, idempotency checks, and check mode.
- An **info module** (`alicloud_<resource>_info.py`) for listing and fetching resource facts.

Both use the Alibaba Cloud OpenAPI (tea-openapi SDK) via `AliCloudModuleBase` in [stevefulme1.alicloud](https://github.com/stevefulme1/ansible-alicloud-collection).

## Quick start

```bash
# Install dependencies
pip install jinja2 pyyaml

# Validate all definitions
python3 -m generator -d definitions/ --validate

# Generate modules
python3 -m generator -d definitions/ -o output/

# Generate a single resource
python3 -m generator -d definitions/ -o output/ -r alicloud_ecs_instance

# Preview without writing files
python3 -m generator -d definitions/ --dry-run
```

## Project structure

```
ansible-alicloud-magic-modules/
├── generator/
│   ├── cli.py              # CLI entry point (argparse)
│   ├── parser.py           # YAML -> ResourceDefinition dataclass
│   ├── renderer.py         # Jinja2 rendering with custom filters
│   ├── utils.py            # Shared utilities (snake_to_pascal, etc.)
│   └── templates/
│       ├── module.py.j2        # CRUD module template
│       └── module_info.py.j2   # Info/facts module template
├── definitions/            # YAML resource definitions
├── output/                 # Generated modules
├── tests/                  # pytest test suite
├── noxfile.py              # CI sessions (tests, generate, lint, sanity, validate, ci)
├── pyproject.toml
└── LICENSE
```

## Writing a resource definition

Each YAML file in `definitions/` describes one Alibaba Cloud resource. Drop a new file there and re-run the generator.

### Minimal example

```yaml
name: EcsSecurityGroup
module_name: alicloud_ecs_securitygroup
description: "Manage Alibaba Cloud ECS security groups"
product: Ecs
api_version: "2014-05-26"
create_action: CreateSecurityGroup
delete_action: DeleteSecurityGroup
describe_action: DescribeSecurityGroups
id_field: SecurityGroupId

properties:
  security_group_name:
    type: str
    required: false
    description: "The name of the security group."
    updatable: true
  vpc_id:
    type: str
    required: false
    description: "The VPC ID."
    updatable: false
```

### Full example with choices, no_log, and suboptions

```yaml
name: EcsInstance
module_name: alicloud_ecs_instance
description: "Manage Alibaba Cloud ECS compute instances"
product: Ecs
api_version: "2014-05-26"
create_action: RunInstances
update_action: ModifyInstanceAttribute
delete_action: DeleteInstance
describe_action: DescribeInstances
list_action: DescribeInstances
id_field: InstanceId
name_field: InstanceName

properties:
  instance_type:
    type: str
    required: true
    description: "The instance type (e.g., ecs.g6.large)."
    updatable: false
  image_id:
    type: str
    required: true
    description: "The image ID."
    updatable: false
  password:
    type: str
    no_log: true
    description: "The instance password."
  internet_charge_type:
    type: str
    choices: [PayByTraffic, PayByBandwidth]
    description: "Billing method for network usage."
  tags:
    type: list
    elements: dict
    description: "Instance tags."
    suboptions:
      key:
        type: str
        required: true
      value:
        type: str
```

### Definition schema reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | str | **required** | PascalCase resource name for class names |
| `module_name` | str | **required** | snake_case Ansible module name (`alicloud_` prefix) |
| `description` | str | `""` | One-line summary for DOCUMENTATION |
| `product` | str | **required** | Alibaba Cloud product code (Ecs, Vpc, Rds, Oss, Slb, etc.) |
| `api_version` | str | **required** | OpenAPI version string (e.g., `"2014-05-26"`) |
| `create_action` | str | `""` | OpenAPI action to create the resource |
| `update_action` | str | `""` | OpenAPI action to update the resource |
| `delete_action` | str | `""` | OpenAPI action to delete the resource |
| `describe_action` | str | `""` | OpenAPI action to describe/get the resource |
| `list_action` | str | `""` | OpenAPI action to list resources |
| `id_field` | str | `""` | API response field containing the resource ID |
| `name_field` | str | `""` | API response field containing the resource name |
| `endpoint_template` | str | `""` | Custom endpoint pattern (default: auto-discovery) |
| `generate_info` | bool | `true` | Whether to generate an `_info` module |
| `author` | str | auto | Author line in DOCUMENTATION |
| `doc_url` | str | `""` | Link in DOCUMENTATION seealso |

### Property fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | str | `str` | Ansible type: `str`, `int`, `float`, `bool`, `list`, `dict` |
| `required` | bool | `false` | Whether the parameter is required |
| `description` | str | `""` | Shown in module DOCUMENTATION |
| `default` | any | -- | Default value |
| `choices` | list | -- | Allowed values |
| `api_field` | str | auto | Alibaba Cloud API parameter name (auto-converted from snake_case to PascalCase if omitted) |
| `updatable` | bool | `true` | Whether the field can be changed after creation |
| `no_log` | bool | `false` | Hide value from logs (for passwords, secrets) |
| `elements` | str | -- | Element type for `type: list` (e.g., `str`, `dict`) |
| `suboptions` | dict | -- | Nested option spec for `list`/`dict` with `elements: dict` |

## Alibaba Cloud API patterns

### RPC vs ROA

Most Alibaba Cloud services use **RPC-style** APIs with flat query parameters:

```
https://ecs.cn-hangzhou.aliyuncs.com/?Action=DescribeInstances&RegionId=cn-hangzhou
```

Some newer services (Container Service, Log Service) use **ROA-style** REST APIs with path-based routing:

```
GET /clusters/{ClusterId}
```

The generator produces modules targeting the **RPC** pattern by default, using the `tea-openapi` SDK to handle authentication (AccessKey), signing, and request construction.

### Region-based endpoints

Alibaba Cloud endpoints follow the pattern `<product>.<region>.aliyuncs.com`:

- `ecs.cn-hangzhou.aliyuncs.com`
- `rds.us-west-1.aliyuncs.com`
- `vpc.ap-southeast-1.aliyuncs.com`

Use `endpoint_template` in definitions to override this for services with non-standard endpoints.

### tea-openapi SDK

Generated modules use the [Alibaba Cloud OpenAPI SDK](https://github.com/aliyun/alibabacloud-python-sdk) (`alibabacloud-tea-openapi`) which provides:

- Automatic AccessKey/STS token authentication
- Request signing (HMAC-SHA1 / HMAC-SHA256)
- Region endpoint discovery
- Retry and error handling

## CI pipeline

The nox-based CI pipeline runs four jobs:

1. **tests** -- pytest with coverage (target: 80%)
2. **generate** -- regenerate all modules from definitions, upload as artifact
3. **lint** -- ansible-lint + pycodestyle on generated modules
4. **sanity** -- ansible-test sanity in a scaffolded collection tree

```bash
# Run the full pipeline locally
nox -s ci

# Run individual sessions
nox -s tests
nox -s generate
nox -s lint
nox -s sanity
nox -s validate
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Requirements

- Python >= 3.12
- `jinja2 >= 3.1`
- `pyyaml >= 6.0`

Generated modules target the [stevefulme1.alicloud](https://github.com/stevefulme1/ansible-alicloud-collection) collection and require `ansible-core >= 2.16`.

## License

GNU General Public License v3.0
