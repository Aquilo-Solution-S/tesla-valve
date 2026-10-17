use serde::Deserialize;

use crate::Invalid;

// region: postcode
/// Five digits. The only way to get one is `Postcode::parse`:
///
/// ```
/// assert!(shop::Postcode::parse("10115").is_ok());
/// ```
///
/// ```compile_fail
/// shop::Postcode(String::from("hello"));
/// ```
pub struct Postcode(String);

impl Postcode {
    pub fn parse(raw: &str) -> Result<Postcode, Invalid> {
        let code = raw.trim();
        if code.len() == 5 && code.bytes().all(|b| b.is_ascii_digit()) {
            Ok(Postcode(code.to_owned()))
        } else {
            Err(Invalid("a postcode is five digits"))
        }
    }
}
// endregion

impl Postcode {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

// region: deserialize
impl<'de> Deserialize<'de> for Postcode {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let raw = String::deserialize(deserializer)?;
        Postcode::parse(&raw).map_err(|Invalid(reason)| serde::de::Error::custom(reason))
    }
}
// endregion
