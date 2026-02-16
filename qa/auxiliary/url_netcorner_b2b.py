def resolve_b2b_nuxt_base_url(server_type: str, server_name: str) -> str:
    env_type = server_type.strip().lower()

    if env_type == "test":
        return f"https://b2b-placeholder-{server_name}.netcorner.pl"
    if env_type == "demo":
        return "https://b2b-placeholder-demo.komputronik.dev"
    if env_type == "prod":
        return "https://b2b-placeholder.pl"
    if env_type == "local":
        return "https://b2b-placeholder.local"
    return ""