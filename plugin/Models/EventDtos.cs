using System.Text.Json.Serialization;

namespace Clutchboard.Models;

public class PluginConfig
{
    [JsonPropertyName("ApiUrl")]  public string ApiUrl    { get; set; } = "http://localhost:8000";
    [JsonPropertyName("ApiSecret")] public string ApiSecret { get; set; } = "";
}

public class KillEventDto
{
    [JsonPropertyName("type")]               public string  Type             { get; set; } = "kill";
    [JsonPropertyName("match_id")]           public string  MatchId          { get; set; } = "";
    [JsonPropertyName("round_number")]       public int     RoundNumber      { get; set; }
    [JsonPropertyName("killer_steam_id")]    public long?   KillerSteamId    { get; set; }
    [JsonPropertyName("victim_steam_id")]    public long    VictimSteamId    { get; set; }
    [JsonPropertyName("assister_steam_id")]  public long?   AssisterSteamId  { get; set; }
    [JsonPropertyName("weapon")]             public string  Weapon           { get; set; } = "";
    [JsonPropertyName("headshot")]           public bool    Headshot         { get; set; }
    [JsonPropertyName("penetrated")]         public bool    Penetrated       { get; set; }
    [JsonPropertyName("noscope")]            public bool    Noscope          { get; set; }
    [JsonPropertyName("thrusmoke")]          public bool    Thrusmoke        { get; set; }
    [JsonPropertyName("attacker_blind")]     public bool    AttackerBlind    { get; set; }
}

public class DamageEventDto
{
    [JsonPropertyName("type")]               public string Type              { get; set; } = "damage";
    [JsonPropertyName("match_id")]           public string MatchId           { get; set; } = "";
    [JsonPropertyName("round_number")]       public int    RoundNumber       { get; set; }
    [JsonPropertyName("attacker_steam_id")]  public long?  AttackerSteamId   { get; set; }
    [JsonPropertyName("victim_steam_id")]    public long   VictimSteamId     { get; set; }
    [JsonPropertyName("weapon")]             public string Weapon            { get; set; } = "";
    [JsonPropertyName("damage")]             public int    Damage            { get; set; }
    [JsonPropertyName("damage_armor")]       public int    DamageArmor       { get; set; }
    [JsonPropertyName("hitgroup")]           public string Hitgroup          { get; set; } = "";
}

public class FlashEventDto
{
    [JsonPropertyName("type")]               public string Type             { get; set; } = "flash";
    [JsonPropertyName("match_id")]           public string MatchId          { get; set; } = "";
    [JsonPropertyName("round_number")]       public int    RoundNumber      { get; set; }
    [JsonPropertyName("thrower_steam_id")]   public long?  ThrowerSteamId   { get; set; }
    [JsonPropertyName("blinded_steam_id")]   public long?  BlindedSteamId   { get; set; }
    [JsonPropertyName("blind_duration")]     public float  BlindDuration    { get; set; }
    [JsonPropertyName("is_teammate")]        public bool   IsTeammate        { get; set; }
}

public class UtilityEventDto
{
    [JsonPropertyName("type")]         public string Type      { get; set; } = "utility";
    [JsonPropertyName("match_id")]     public string MatchId   { get; set; } = "";
    [JsonPropertyName("round_number")] public int    RoundNumber { get; set; }
    [JsonPropertyName("steam_id")]     public long?  SteamId   { get; set; }
    [JsonPropertyName("event_type")]   public string EventType { get; set; } = "";
    [JsonPropertyName("damage")]       public int    Damage    { get; set; }
}

public class WeaponFireEventDto
{
    [JsonPropertyName("type")]         public string Type        { get; set; } = "weapon_fire";
    [JsonPropertyName("match_id")]     public string MatchId     { get; set; } = "";
    [JsonPropertyName("round_number")] public int    RoundNumber { get; set; }
    [JsonPropertyName("steam_id")]     public long?  SteamId     { get; set; }
    [JsonPropertyName("weapon")]       public string Weapon      { get; set; } = "";
}

public class RoundStartEventDto
{
    [JsonPropertyName("type")]         public string Type        { get; set; } = "round_start";
    [JsonPropertyName("match_id")]     public string MatchId     { get; set; } = "";
    [JsonPropertyName("round_number")] public int    RoundNumber { get; set; }
}

public class RoundEndEventDto
{
    [JsonPropertyName("type")]             public string  Type            { get; set; } = "round_end";
    [JsonPropertyName("match_id")]         public string  MatchId         { get; set; } = "";
    [JsonPropertyName("round_number")]     public int     RoundNumber     { get; set; }
    [JsonPropertyName("winner")]           public string  Winner          { get; set; } = "";
    [JsonPropertyName("win_reason")]       public string  WinReason       { get; set; } = "";
    [JsonPropertyName("duration_seconds")] public int?    DurationSeconds { get; set; }
}

public class MatchStartEventDto
{
    [JsonPropertyName("type")]       public string Type       { get; set; } = "match_start";
    [JsonPropertyName("match_id")]   public string MatchId    { get; set; } = "";
    [JsonPropertyName("map_name")]   public string MapName    { get; set; } = "";
    [JsonPropertyName("started_at")] public string StartedAt  { get; set; } = "";
}

public class MatchEndEventDto
{
    [JsonPropertyName("type")]             public string              Type            { get; set; } = "match_end";
    [JsonPropertyName("match_id")]         public string              MatchId         { get; set; } = "";
    [JsonPropertyName("t_score")]          public int                 TScore          { get; set; }
    [JsonPropertyName("ct_score")]         public int                 CtScore         { get; set; }
    [JsonPropertyName("duration_seconds")] public int?                DurationSeconds { get; set; }
    [JsonPropertyName("player_teams")]     public Dictionary<string, string> PlayerTeams { get; set; } = new();
}

public class PlayerConnectEventDto
{
    [JsonPropertyName("type")]         public string  Type        { get; set; } = "player_connect";
    [JsonPropertyName("steam_id")]     public long    SteamId     { get; set; }
    [JsonPropertyName("display_name")] public string  DisplayName { get; set; } = "";
    [JsonPropertyName("avatar_url")]   public string? AvatarUrl   { get; set; }
}
