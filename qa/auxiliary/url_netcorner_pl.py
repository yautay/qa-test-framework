def resolve_pl_nuxt_base_url(server_type: str, server_name: str) -> str:
    env_type = server_type.strip().lower()

    if env_type == "test":
        return f"https://komputronik-{server_name}.netcorner.pl"
    if env_type == "demo":
        return "https://sklep3-demo.komputronik.dev"
    if env_type == "prod":
        return "https://komputronik.pl"
    if env_type == "local":
        return "https://komputronik.local"
    return ""
