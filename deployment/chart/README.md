# Kubernetes deployment of WES-ELIXIR

Deploy with helm:

```bash
helm install . --generate-name -f <netrc-yaml-auth>
```

Here `<netrc-yaml-auth>` should contain:

```yaml
wes:
  netrcMachine: <machine>
  netrcLogin: <login>
  netrcPassword: <password>
```

## Variable documentation

The list is non-exhaustive.

| Variable | meaning | default |
|:---------|:--------|:--------|
| .clusterType | If not kubernetes, assume openshift and use Route object | `kubernetes` |
| .applicationDomain | Application DNS name |  |
