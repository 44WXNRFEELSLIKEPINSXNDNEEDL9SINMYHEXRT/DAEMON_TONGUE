from huggingface_hub import HfApi

MODEL_DIR  = "./DAEMON_TONGUE_JUDGE"
HF_REPO    = "44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE_JUDGE"

api = HfApi()
api.create_repo(HF_REPO, exist_ok=True)
api.upload_folder(
    folder_path = MODEL_DIR,
    repo_id     = HF_REPO
)
print(f"Pushed to huggingface.co/{HF_REPO}")