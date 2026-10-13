# Lab 3: settings needed before the first deployment

The pipeline is prepared locally. The student created the Azure resources listed
below; they still serve Microsoft's placeholder page because OceENS has not been
deployed. Configure OIDC, the resource-group role, and the staging Environment
before merging the workflow into the fork's default branch. Configure production
before manually promoting an image; the teacher's production values arrive in
lab step 5.

## Accounts and course information

1. The active subscription is **Azure subscription 1**, an Azure free trial
   activated 13 October 2026. Keep its spending protection: do not upgrade to
   pay-as-you-go or remove the spending limit. The account showed USD 200 trial
   credit, expiring 12 November 2026. The B1 plan consumes this credit; resources
   stop when the credit is exhausted or expires without an upgrade. The portal's
   estimate for the shared plan was USD 13.14/month; this is not a permanently free
   service.
2. [Mistral Studio](https://console.mistral.ai/) has been opened, but assume no API
   key is available. Create a key under API keys when configuring staging. See
   [Mistral's first-request guide](https://docs.mistral.ai/getting-started/quickstarts/developer/first-api-request).
   Enter it directly as a GitHub Environment secret. Do not paste it in the chat
   or a tracked file.
3. Get the production dev sign-in key and the production LLM endpoint from the
   instructor's Teams message. The endpoint is used only in lab step 5.

## Azure resources

The student created these resources in [Azure Portal](https://portal.azure.com/):

| Resource | Current value |
|---|---|
| Subscription | Azure subscription 1 (`29b24240-e96d-4e32-9a00-34ac3b61ea65`) |
| Resource group | `rg-oceens-lab3` |
| Shared App Service plan | `asp-oceens-lab3`, Linux Basic B1, France Central, one instance |
| Staging app | `oceens-gdm-staging-29b24240` |
| Staging URL | <https://oceens-gdm-staging-29b24240-gmexdhgwbqerh5g2.francecentral-01.azurewebsites.net/> |
| Production app | `oceens-gdm-production-29b24240` |
| Production URL | <https://oceens-gdm-production-29b24240-cfetesgre9cugpdy.francecentral-01.azurewebsites.net/> |

Both apps share one instance and the B1 plan. Each instance would otherwise have
its own SQLite file and summaries daemon. The deployment action sets **Always On**.
The current app image is Microsoft's placeholder, not OceENS.

Use the classic single-container Docker configuration supported by the pipeline
(`linuxFxVersion=DOCKER|...`), not a sidecar configuration. The app listens on port
8000. GHCR's package must be public for the current deploy action to pull it
without registry credentials. Its first publication creates it; set its package
visibility to public, then rerun the failed staging job if necessary. Source and
image contain no secrets.

Keep Azure's secure unique default hostname enabled. Its public address may include
a generated suffix and a region. The deployment action reads `defaultHostName`
from Azure and uses that actual address for its health check and the GitHub
Environment link. Copy the actual production URL when writing `production.json`.

The pipeline uses a Microsoft Entra application and its service principal with
GitHub OIDC; it stores no Azure client secret or publish profile. Following
[Azure's OIDC setup guide](https://learn.microsoft.com/en-us/azure/app-service/deploy-github-actions?tabs=openid%2Capplevel),
create the identity and give it the **Website Contributor** role on the course
resource group. The fork was created after GitHub's July 15, 2026 immutable
subject rollout and currently uses its default immutable OIDC subject format.
GitHub's public IDs for this owner and repository are `257501862` and
`1387054607`. Add two federated credentials for this repository, using the
environment scenario so each subject is scoped to one GitHub Environment:

| GitHub Environment | OIDC subject |
|---|---|
| staging | `repo:demontgolfierguillaume-prog@257501862/OceENS@1387054607:environment:staging` |
| production | `repo:demontgolfierguillaume-prog@257501862/OceENS@1387054607:environment:production` |

For both, the issuer is `https://token.actions.githubusercontent.com` and the
audience is `api://AzureADTokenExchange`. Keep the application/client ID, directory/
tenant ID and subscription ID for GitHub's variables below. Your account needs
permission to register the identity and assign its role; if the school tenant
blocks either operation, ask the instructor for the course's supported identity.

## GitHub Environments

In [the fork's environments settings](https://github.com/demontgolfierguillaume-prog/OceENS/settings/environments),
create `staging` and `production`. Restrict deployment branches to
`course-2026-fallback-clean-bench`, the current default branch. Configure these
names **in each environment**, not as repository-wide shared session secrets:

| Name | Kind | Value to supply |
|---|---|---|
| `AZURE_CLIENT_ID` | Variable | `e03f4097-ea71-49d1-b42d-b088cff98013` |
| `AZURE_TENANT_ID` | Variable | `07c72520-e645-4679-8f55-dc611c975a02` |
| `AZURE_SUBSCRIPTION_ID` | Variable | `29b24240-e96d-4e32-9a00-34ac3b61ea65` |
| `AZURE_RESOURCE_GROUP` | Variable | `rg-oceens-lab3` |
| `AZURE_WEBAPP_NAME` | Variable | Staging: `oceens-gdm-staging-29b24240`; production: `oceens-gdm-production-29b24240` |
| `SECRET_KEY` | Secret | A fresh random session signing secret, different in each environment |
| `DEV_LOGIN_KEY` | Secret | Your own staging key; the instructor's production key |
| `MISTRAL_API_KEY` | Secret | Your Mistral key |
| `DEFAULT_PROVIDER_BASE_URL` | Secret, production only | In step 5, the instructor's full endpoint; omit initially to use Mistral directly |
| `POSTHOG_PROJECT_TOKEN` | Secret | Your EU project's `phc_...` token; omit to leave telemetry off |

Generate the random session keys locally in a terminal and enter them directly in
GitHub. Never copy `.env.example` values into these secrets. Do not put keys into
shell command history or the progression file.

The action supplies `AUTH_MODE=dev`, `DEFAULT_PROVIDER_API_TYPE=openai`,
`DEFAULT_PROVIDER_MODEL=ministral-14b-latest`,
`DEFAULT_PROVIDER_KEY_ENV=MISTRAL_API_KEY`, `RUN_SUMMARIES_DAEMON=1`,
`LOCAL_DATABASE_DIR=/app/database`, `WEBSITES_PORT=8000` and
`WEBSITES_ENABLE_APP_SERVICE_STORAGE=false`. These constants do not need additional
GitHub variables. Provider type/model/key setting are read by the seed on an empty
database. The container's database is ephemeral, so each fresh container seeds
the existing provider name again with its environment's settings.

When `POSTHOG_PROJECT_TOKEN` is present, the action also sets
`POSTHOG_HOST=https://eu.i.posthog.com` and `POSTHOG_ENVIRONMENT` to `staging` or
`production`. Without the token, all three app settings are empty and PostHog remains
off; the application rejects a partial PostHog configuration at startup.

## First run and promotion

After reviewing the workflow, push a branch and open a PR against your fork's
default branch. Its `architecture` and `test` checks must pass. Merge it when the
environments and resources are ready. That pushed merge commit runs the staging
deployment; record its run URL and full SHA after the new revision answers.

On staging, sign in and test the existing provider row in `/backend/providers`.
Then, under **Actions → Architecture Check → Run workflow**, select the default
branch and run the manual promotion. Before a successful staging deployment,
selection fails deliberately: no image has yet been validated for production.

The application reports errors and OTLP logs to PostHog when its settings are
configured. The staging exception proof, production log proof, saved query and Error
Ledger are student actions later in the lab.

## References

- [Course worked example: MATHutrice #100](https://github.com/EPF-MDE/MATHutrice/pull/100)
- [App Service custom container configuration](https://learn.microsoft.com/en-us/azure/app-service/configure-custom-container)
- [GitHub OIDC with Azure](https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-azure)
