This directory contains the configuration files to run the Layers Project backend system using the Nomad cluster manager. We use Nomad because Kubernetes is overkill, and administering a kubernetes cluster is difficult and a ton of work. That said, the commitment to Nomad is pretty weak at this time; if there is a good argument for something different (and a willingness to contribute to its implementation), we might port the project.

That said, the main requirements at this point in the project's lifecycle are:

- Must have a viable local dev workflow
- Simple and well-documented configuration format
- Administration, especially before we reach scale, shouldn't be a big time sink
- Well adopted, with convincing case for longevity and continued improvement

Nomad meets all of these requirements. As the project matures, these needs may change and we can re-evaluate.
