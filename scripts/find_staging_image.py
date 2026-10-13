"""Select an image from successful staging jobs, never from the app's settings."""

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def find_staging_image(repository, branch, get_page, log=print):
    """Return the newest pushed commit whose staging deploy succeeded.

    get_page reads a GitHub REST path. Pagination includes older runs and all
    jobs, so a failed latest deploy cannot hide an earlier successful one.
    """
    page = 1
    while True:
        query = urlencode({"branch": branch, "event": "push", "per_page": 100, "page": page})
        runs = get_page(
            f"repos/{repository}/actions/workflows/architecture.yml/runs?{query}"
        )["workflow_runs"]
        if not runs:
            raise RuntimeError(f"No successful staging deploy on {branch}; nothing to promote")
        for run in runs:
            result = None
            job_page = 1
            while True:
                jobs = get_page(
                    f"repos/{repository}/actions/runs/{run['id']}/jobs"
                    f"?filter=latest&per_page=100&page={job_page}"
                )["jobs"]
                deploys = [job for job in jobs if job["name"] == "deploy to staging"]
                if deploys:
                    result = deploys[0].get("conclusion")
                    break
                if len(jobs) < 100:
                    break
                job_page += 1
            if result == "success":
                sha = run["head_sha"]
                log(f"Selected {run['html_url']}, commit {sha}: staging deploy passed")
                return f"ghcr.io/{repository.lower()}:{sha}"
            log(f"Skipped run {run['id']}, commit {run['head_sha']}: staging {result or 'has no result'}")
        page += 1


def main():
    repository = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GH_TOKEN"]
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")

    def get_page(path):
        request = Request(f"{api_url}/{path}", headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    image = find_staging_image(repository, os.environ["DEPLOY_BRANCH"], get_page)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"image={image}\n")


if __name__ == "__main__":
    main()
