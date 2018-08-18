export interface Settings {
    DEBUG_PORT: number;
    MEDIA_URL: string;
    STATIC_URL: string;
    DEBUG: boolean;
}

export interface Message {
  level: number;
  level_tag: string;
  message: string;
}
