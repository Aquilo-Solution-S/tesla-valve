// expect: fn_params_excessive_bools
pub fn ship(express: bool, gift: bool) -> u8 {
    u8::from(express) + u8::from(gift)
}
