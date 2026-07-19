use crate::cbck::{encode_cbck, parse_cbck, CBCKPayload};

pub fn complete_cbck_encode(bgra: &[u8], width: u32, height: u32) -> Vec<u8> {
    encode_cbck(bgra, width, height, 4, true)
}

pub fn complete_cbck_decode(data: &[u8]) -> Result<CBCKPayload, &'static str> {
    parse_cbck(data)
}
