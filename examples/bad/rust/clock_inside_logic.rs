// expect: disallowed_methods
pub fn today() -> chrono::NaiveDate {
    chrono::Utc::now().date_naive()
}
