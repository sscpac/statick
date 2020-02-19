# Templates

These are the basic files you need to drop into a project in order to make it
easy to run Statick as part of a Jenkins build.

## Dockerfile

The Dockerfile contains the minimum set of packages and python modules to run
Statick as part of a Jenkins build.
You can either copy it into your software's version control and add the dependencies
needed to build your software or you can inherit from this Dockerfile using a `FROM`
tag in your own Dockerfile.

## Jenkinsfile

As with the Dockerfile, this is a minimum example for how to check out and run
Statick as part of a Jenkins build.
It assumes the presence of a valid Dockerfile and that you have a Jenkins node
with the "docker" label.

## statick_config

You can drop `statick_config` into your repository and point Statick's
`--user-paths` argument at that directory in order to override the default
Statick configurations for your repository.
Of particular interest is `profile.yaml`, which is used to set the default
analysis profile for your repository.
