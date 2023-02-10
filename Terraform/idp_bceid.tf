resource "keycloak_oidc_identity_provider" "bceid" {
  realm                         = data.keycloak_realm.bcregistry_realm.id
  alias                         = "bceid"
  display_name                  = "BCeID"
  enabled                       = true
  store_token                   = false
  trust_email                   = false
  first_broker_login_flow_alias = "first broker login"
  sync_mode                     = "FORCE"
  authorization_url             = "${var.environment.base_url}/realms/standard/protocol/openid-connect/auth?kc_idp_hint=bceidboth"
  token_url                     = "${var.environment.base_url}/realms/standard/protocol/openid-connect/token"
  logout_url                    = "${var.environment.base_url}/realms/standard/protocol/openid-connect/logout"
  backchannel_supported         = true
  user_info_url                 = "${var.environment.base_url}/realms/standard/protocol/openid-connect/userinfo"
  client_id                     = var.keycloak_idp_bceid_client.id
  client_secret                 = var.keycloak_idp_bceid_client.secret
  issuer                        = "${var.environment.base_url}/realms/standard"
  validate_signature            = true
  default_scopes                = ""

  jwks_url = "${var.environment.base_url}/realms/standard/protocol/openid-connect/certs"
  extra_config = {
    "clientAuthMethod" = "client_secret_post"
    "prompt"           = "unspecified"
  }
}

resource "keycloak_user_template_importer_identity_provider_mapper" "bceid_username_importer" {
  realm                   = data.keycloak_realm.bcregistry_realm.id
  name                    = "username"
  identity_provider_alias = keycloak_oidc_identity_provider.bceid.alias
  template                = "$${CLAIM.bceid_username}@$${ALIAS}"
  extra_config = {
    syncMode = "FORCE"
  }
}

resource "keycloak_hardcoded_attribute_identity_provider_mapper" "bceid_login_source" {
  realm                   = data.keycloak_realm.bcregistry_realm.id
  name                    = "loginSource"
  identity_provider_alias = keycloak_oidc_identity_provider.bceid.alias
  attribute_name          = "source"
  attribute_value         = "BCEID"
  user_session            = false
  extra_config = {
    syncMode = "FORCE"
  }
}

resource "keycloak_attribute_importer_identity_provider_mapper" "bceid_displayname" {
  realm                   = data.keycloak_realm.bcregistry_realm.id
  name                    = "displayName"
  claim_name              = "display_name"
  identity_provider_alias = keycloak_oidc_identity_provider.bceid.alias
  user_attribute          = "displayName"
  extra_config = {
    syncMode = "FORCE"
  }
}

resource "keycloak_attribute_importer_identity_provider_mapper" "bceid_idp_userid" {
  realm                   = data.keycloak_realm.bcregistry_realm.id
  name                    = "idp_userid"
  claim_name              = "bceid_user_guid"
  identity_provider_alias = keycloak_oidc_identity_provider.bceid.alias
  user_attribute          = "idp_userid"
  extra_config = {
    syncMode = "FORCE"
  }
}
