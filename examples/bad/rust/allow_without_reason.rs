// expect: allow_attributes
// expect: allow_attributes_without_reason
#[allow(clippy::unwrap_used)]
pub fn berlin() -> crate::Postcode {
    crate::Postcode::parse("10115").unwrap()
}
