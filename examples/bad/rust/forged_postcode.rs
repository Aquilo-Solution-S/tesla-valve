// expect: E0423
pub fn forged() -> crate::Postcode {
    crate::Postcode(String::from("hello"))
}
