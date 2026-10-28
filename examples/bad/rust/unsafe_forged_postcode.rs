// expect: unsafe-code
pub fn forged() -> crate::Postcode {
    unsafe { std::mem::transmute::<String, crate::Postcode>(String::from("hello")) }
}
