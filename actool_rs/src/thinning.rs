pub static IDIOMS: &[(&str, u16)] = &[
    ("universal", 0),
    ("iphone", 1),
    ("phone", 1),
    ("ipad", 2),
    ("pad", 2),
    ("tv", 3),
    ("car", 4),
    ("carplay", 4),
    ("watch", 5),
    ("marketing", 6),
    ("mac", 7),
    ("vision", 8),
    ("visionos", 8),
];

#[derive(Debug, Clone, Default)]
pub struct ThinningOptions {
    pub idiom: Option<String>,
    pub scale: Option<u16>,
    pub appearance: Option<u16>,
    pub keep_fallbacks: bool,
}

impl ThinningOptions {
    pub fn new() -> Self {
        Self {
            idiom: None,
            scale: None,
            appearance: None,
            keep_fallbacks: true,
        }
    }
}
