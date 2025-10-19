# Deploy Using GitHub Actions (Free Alternative)

**Use GitHub Actions while waiting for Azure DevOps parallelism to be fixed.**

GitHub provides **2,000 free minutes/month** for public repos and **500 minutes/month** for private repos.

---

## Quick Setup (10 minutes)

### Step 1: Push to GitHub

```bash
# Add GitHub as additional remote (keep Azure DevOps too)
git remote add github https://github.com/<your-username>/<repo-name>.git

# Or create new repo on GitHub first, then:
# Go to https://github.com/new
# Create repo: ltc-insurance-api
# Copy the URL

# Push to GitHub
git push github main
```

---

### Step 2: Add Secrets to GitHub

1. Go to your GitHub repo
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Add these secrets:

**Secret 1:**
```
Name: SNOWFLAKE_USER
Value: VIDYASURESH
```

**Secret 2:**
```
Name: SNOWFLAKE_PASSWORD
Value: WskexGhNNFh8bwf
```

---

### Step 3: Trigger Workflow

**Option A: Automatic (push code)**
```bash
# Make any change
git commit --allow-empty -m "Trigger build"
git push github main
```

**Option B: Manual**
1. Go to repo on GitHub
2. Click **"Actions"** tab
3. Select **"Deploy to Snowflake SPCS"** workflow
4. Click **"Run workflow"** → **"Run workflow"**

---

### Step 4: Monitor Build

1. Go to **Actions** tab in GitHub
2. Click on the running workflow
3. Watch the build progress (~5-10 minutes)

**Expected output:**
```
✅ Image pushed successfully!
Version: 20241019-015630
Image: bnmbckj-vi07646.registry.snowflakecomputing.com/ltc_api_repo/images/fastapi_repo/ltc-api:20241019-015630
```

**Save the version tag** from the output!

---

### Step 5: Verify in Snowflake

```sql
USE DATABASE LTC_API_REPO;
USE SCHEMA IMAGES;

SHOW IMAGES IN IMAGE REPOSITORY FASTAPI_REPO;
-- You should see your image with the version tag
```

---

## After Image is Built

Continue with creating the service in Snowflake - see **AZURE_DEVOPS_DEPLOYMENT.md** Step 5.1 onwards.

---

## Benefits

✅ **Free tier** - 2,000 minutes/month (public repo) or 500 min/month (private)  
✅ **Fast** - Similar speed to Azure DevOps  
✅ **No waiting** - Works immediately  
✅ **Keep both** - Can use GitHub for builds, Azure DevOps for code

---

## Cost Comparison

| Platform | Free Tier | Build Time | Cost After Free |
|----------|-----------|------------|-----------------|
| GitHub Actions | 2,000 min/month (public)<br>500 min/month (private) | ~8 minutes/build | $0.008/min |
| Azure DevOps | 1,800 min/month (but needs parallelism) | ~8 minutes/build | Varies |

**For ~10 builds/month:** GitHub free tier is plenty!

---

## Alternative: One-Time Manual Build

If you have access to ANY machine with Docker (colleague's laptop, cloud VM, etc.):

```bash
# On machine with Docker:
git clone https://dev.azure.com/vidyalakshmiv97/FASTAPI/_git/FASTAPI
cd FASTAPI

# Build
docker build -t ltc-api:v1.0.0 .

# Tag
docker tag ltc-api:v1.0.0 \
  bnmbckj-vi07646.registry.snowflakecomputing.com/ltc_api_repo/images/fastapi_repo/ltc-api:v1.0.0

# Login and push
docker login bnmbckj-vi07646.registry.snowflakecomputing.com -u VIDYASURESH
docker push bnmbckj-vi07646.registry.snowflakecomputing.com/ltc_api_repo/images/fastapi_repo/ltc-api:v1.0.0
```

---

**Recommendation:** Use GitHub Actions for now - it's the fastest way forward!

Want me to help you set up GitHub Actions?

