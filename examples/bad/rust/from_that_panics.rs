// expect: fallible_impl_from
impl From<&str> for crate::Postcode {
    fn from(raw: &str) -> Self {
        match crate::Postcode::parse(raw) {
            Ok(postcode) => postcode,
            Err(crate::Invalid(reason)) => panic!("{reason}"),
        }
    }
}
