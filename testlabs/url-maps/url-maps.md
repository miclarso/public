# url maps

gxlb and rilb url maps

```
# output url map to local yaml file
gcloud compute url-maps describe URL-MAP-NAME > URL-MAP-FILE.yaml
```

```
# input local yaml file to url map
gcloud compute url-maps import URL-MAP-NAME \
  --source="/local/file/path/URL-MAP-FILE.yaml"
```

## routeRules

### [url-map-l7-gxlb-new-23.yaml](/testlabs/url-maps/yaml/url-map-l7-gxlb-new-23.yaml) :boom:

- 5x path matchers
  - routeRules: prefixMatch: x# /prefixes
  - routeAction: urlRewrite: hostRewrite: per backend service
- 9x backend services per path matcher

```
1- 3/3/3/3/3/3/3/3/3
2- 3/3/3/3/3/3/3/3/3
3- 3/3/3/3/3/3/3/3/3
4- 3/3/3/3/3/3/3/3/3
5- 3/3/3/3/3/3/3/4/868
```

- => 1001 :boom:

### [url-map-l7-gxlb-new-22.yaml](/testlabs/url-maps/yaml/url-map-l7-gxlb-new-22.yaml) :exclamation:

- 5x path matchers
  - routeRules: - prefixMatch: (per line) x# /prefixes
  - routeAction: urlRewrite: hostRewrite: per backend service
- 9x backend services per path matcher

```
1- 3/3/3/3/3/3/3/3/3
2- 3/3/3/3/3/3/3/3/3
3- 3/3/3/3/3/3/3/3/3
4- 3/3/3/3/3/3/3/3/3
5- 3/3/3/3/3/3/3/3/868
```

- => 1000 :exclamation:

### [url-map-l7-gxlb-new-21.yaml](/testlabs/url-maps/yaml/url-map-l7-gxlb-new-21.yaml)

- 5x path matchers
  - routeRules: - prefixMatch: (per line) x# /prefixes
  - routeAction: urlRewrite: hostRewrite: per backend service
- 9x backend services per path matcher

```
1- 3/3/3/3/3/3/3/3/3
2- 3/3/3/3/3/3/3/3/3
3- 3/3/3/3/3/3/3/3/3
4- 3/3/3/3/3/3/3/3/3
5- 3/3/3/3/3/3/3/3/3
```

- => 135


### [url-map-l7-gxlb-new-11.yaml](/testlabs/url-maps/yaml/url-map-l7-gxlb-new-11.yaml)

- 5x path matchers
  - routeRules: prefixMatch: x# /prefixes
  - routeAction: urlRewrite: hostRewrite: per backend service
- 9x backend services per path matcher

```
1- 3/3/3/3/3/3/3/3/3
2- 3/3/3/3/3/3/3/3/3
3- 3/3/3/3/3/3/3/3/3
4- 3/3/3/3/3/3/3/3/3
5- 3/3/3/3/3/3/3/3/3
```

- => 135

NOTE: each "- prefixMatch:" line has max size of 1024 characters (eg, ~50x basepaths), however that syntax merges basepaths on the same line into a single comma separated value and won't match and route appropriately

```
$ yq '.pathMatchers[].routeRules[].matchRules[].prefixMatch'   url-map-l7-gxlb-prefix-verticals-not.yaml
/vert01/api1, /vert01/api2, /vert01/api3, /vert01/api4, /vert01/api5
/vert02/api1
/vert02/api2
```

## pathRules

### [url-map-l7-gxlb-new-03.yaml](/testlabs/url-maps/yaml/url-map-l7-gxlb-new-03.yaml) :boom:

- 5x path matchers
  - pathRules: x# /paths
  - routeAction: urlRewrite: hostRewrite: per backend service
- 9x backend services per path matcher

```
1- 3/3/3/3/3/3/3/3/3
2- 4/4/3/3/3/3/3/3/3
3- 3/3/3/3/3/3/3/3/3
4- 3/3/3/3/3/3/3/3/3
5- 3/3/3/3/3/3/3/4/868
```

- => 1001 :boom:

```log
ERROR: (gcloud.compute.url-maps.import) HTTPError 400: Invalid value for field 'resource.pathMatchers[0]': '
{  "name": "path-matcher-1",  "defaultService": "https://www.googleapis.com/compute/v1/projects/${PROJECT_ID}/...'. 
Total number of paths is 1001, which exceeds the limit 1000.
```

### [url-map-l7-gxlb-new-02.yaml](/testlabs/url-maps/yaml/url-map-l7-gxlb-new-02.yaml) :exclamation:

- 5x path matchers
  - pathRules: x# /paths
  - routeAction: urlRewrite: hostRewrite: per backend service
- 9x backend services per path matcher

```
1- 3/3/3/3/3/3/3/3/3
2- 4/3/3/3/3/3/3/3/3
3- 3/3/3/3/3/3/3/3/3
4- 3/3/3/3/3/3/3/3/3
5- 3/3/3/3/3/3/3/3/868
```

- => 1000 :exclamation:

### [url-map-l7-gxlb-new-01.yaml](/testlabs/url-maps/yaml/url-map-l7-gxlb-new-01.yaml)
- 5x path matchers
  - pathRules: x# /paths
  - routeAction: urlRewrite: hostRewrite: per backend service
- 9x backend services per path matcher

```
1- 3/3/3/3/3/3/3/3/3
2- 3/3/3/3/3/3/3/3/3
3- 3/3/3/3/3/3/3/3/3
4- 3/3/3/3/3/3/3/3/3
5- 3/3/3/3/3/3/3/3/3
```

- => 135