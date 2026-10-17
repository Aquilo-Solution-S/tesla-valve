// expect: unwrap_used
pub fn berlin() -> crate::Postcode {
    crate::Postcode::parse("10115").unwrap()
}
