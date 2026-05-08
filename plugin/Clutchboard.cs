using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes;
using Clutchboard.Models;
using Clutchboard.Services;
using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace Clutchboard;

[MinimumApiVersion(80)]
public class ClutchboardPlugin : BasePlugin
{
    public override string ModuleName    => "Clutchboard";
    public override string ModuleVersion => "1.0.0";
    public override string ModuleAuthor  => "clutchboard";

    private ApiClient _api = null!;
    private string _matchId = string.Empty;
    private string _demoPath = string.Empty;
    private int _currentRound;
    private bool _matchStartSent;
    private bool _isWarmup = true;
    private string _gameDir = string.Empty;
    private readonly Dictionary<ulong, string> _playerTeams = new();
    private readonly Dictionary<ulong, int> _playerMvps = new();
    private readonly Dictionary<int, ulong> _steamIdCache = new(); // entity index → steam id

    public override void Load(bool hotReload)
    {
        var cfg = LoadConfig();
        _api = new ApiClient(cfg.ApiUrl, cfg.ApiSecret);

        // ModuleDirectory = .../csgo/addons/counterstrikesharp/plugins/Clutchboard/
        _gameDir = Path.GetFullPath(Path.Combine(ModuleDirectory, "..", "..", "..", ".."));

        RegisterListener<Listeners.OnClientAuthorized>((slot, steamId) =>
        {
            Logger.LogInformation("[CB] OnClientAuthorized slot={Slot} steamId={SteamId}", slot, steamId.SteamId64);
            _steamIdCache[slot] = steamId.SteamId64;
        });

        RegisterListener<Listeners.OnMapStart>(_ =>
        {
            _matchId = Guid.NewGuid().ToString();
            _demoPath = string.Empty;
            _currentRound = 0;
            _matchStartSent = false;
            _isWarmup = true;
            _playerTeams.Clear();
            _playerMvps.Clear();
            _steamIdCache.Clear();
        });

        RegisterEventHandler<EventWarmupEnd>((@event, _) => { _isWarmup = false; return HookResult.Continue; });
        RegisterEventHandler<EventRoundStart>(OnRoundStart);
        RegisterEventHandler<EventRoundEnd>(OnRoundEnd);
        RegisterEventHandler<EventCsWinPanelMatch>(OnMatchEnd);
        RegisterEventHandler<EventPlayerConnectFull>(OnPlayerConnect);
        RegisterEventHandler<EventPlayerDeath>(OnPlayerDeath);
        RegisterEventHandler<EventPlayerHurt>(OnPlayerHurt);
        RegisterEventHandler<EventFlashbangDetonate>(OnFlashDetonate);
        RegisterEventHandler<EventSmokegrenadeDetonate>(OnSmokeDetonate);
        RegisterEventHandler<EventMolotovDetonate>(OnMolotovDetonate);
        RegisterEventHandler<EventHegrenadeDetonate>(OnHeDetonate);
        RegisterEventHandler<EventWeaponFire>(OnWeaponFire);
        RegisterEventHandler<EventPlayerTeam>(OnPlayerTeam);
        RegisterEventHandler<EventRoundMvp>(OnRoundMvp);
    }

    public override void Unload(bool hotReload)
    {
        _api.Dispose();
    }

    // ── Match lifecycle ───────────────────────────────────────────────────────

    private bool IsWarmup() => _isWarmup;

    private HookResult OnRoundStart(EventRoundStart @event, GameEventInfo _)
    {
        if (IsWarmup()) return HookResult.Continue;

        if (_matchId == string.Empty)
        {
            _matchId = Guid.NewGuid().ToString();
            _matchStartSent = false;
            _playerTeams.Clear();
        }

        if (!_matchStartSent)
        {
            _matchStartSent = true;
            _demoPath = Path.Combine(_gameDir, "csgo", $"{_matchId}.dem");
            Server.ExecuteCommand($"tv_record \"{_matchId}\"");
            EmitConnectedPlayers();
            _api.EnqueueEvent(new MatchStartEventDto
            {
                MatchId   = _matchId,
                MapName   = CurrentMapName(),
                StartedAt = DateTime.UtcNow.ToString("O"),
            });
        }

        _currentRound++;
        _api.EnqueueEvent(new RoundStartEventDto
        {
            MatchId     = _matchId,
            RoundNumber = _currentRound,
        });
        return HookResult.Continue;
    }

    private HookResult OnRoundEnd(EventRoundEnd @event, GameEventInfo _)
    {
        if (_matchId == string.Empty || IsWarmup()) return HookResult.Continue;
        var winner = @event.Winner == 2 ? "T" : "CT";
        _api.EnqueueEvent(new RoundEndEventDto
        {
            MatchId     = _matchId,
            RoundNumber = _currentRound,
            Winner      = winner,
            WinReason   = @event.Reason switch
            {
                7  => "bomb_exploded",
                8  => "bomb_defused",
                12 => "time_expired",
                _  => "elimination",
            },
        });
        return HookResult.Continue;
    }

    private HookResult OnMatchEnd(EventCsWinPanelMatch @event, GameEventInfo _)
    {
        if (_matchId == string.Empty) return HookResult.Continue;
        Server.ExecuteCommand("tv_stoprecord");
        // CS2 takes a moment to flush and close the demo file after tv_stoprecord
        Task.Run(async () => { await Task.Delay(5000); PruneOldDemos(10); });
        var tScore = 0;
        var ctScore = 0;
        foreach (var team in Utilities.FindAllEntitiesByDesignerName<CCSTeam>("cs_team_manager"))
        {
            if (!team.IsValid) continue;
            if (team.TeamNum == 2) tScore = team.Score;
            else if (team.TeamNum == 3) ctScore = team.Score;
        }
        var playerScores = new Dictionary<string, int>();
        foreach (var p in Utilities.GetPlayers())
        {
            if (p == null || !p.IsValid || IsBot(p) || !HasSteamId(p)) continue;
            playerScores[SteamId(p).ToString()] = p.Score;
        }
        var teams = _playerTeams.ToDictionary(kv => kv.Key.ToString(), kv => kv.Value);
        var mvps  = _playerMvps.ToDictionary(kv => kv.Key.ToString(), kv => kv.Value);
        _api.EnqueueEvent(new MatchEndEventDto
        {
            MatchId      = _matchId,
            TScore       = tScore,
            CtScore      = ctScore,
            PlayerTeams  = teams,
            PlayerScores = playerScores,
            PlayerMvps   = mvps,
            DemoPath     = _demoPath,
        });
        _playerTeams.Clear();
        _playerMvps.Clear();
        _matchId = string.Empty;
        _demoPath = string.Empty;
        return HookResult.Continue;
    }

    // ── Player events ─────────────────────────────────────────────────────────

    private ulong SteamId(CCSPlayerController p)
    {
        var sid = p.AuthorizedSteamID?.SteamId64 ?? 0UL;
        if (sid != 0UL) return sid;
        _steamIdCache.TryGetValue((int)p.Slot, out sid);
        return sid;
    }

    private static bool IsBot(CCSPlayerController p) => p.IsBot;

    private bool HasSteamId(CCSPlayerController p) => SteamId(p) != 0UL;

    private void EmitConnectedPlayers()
    {
        foreach (var p in Utilities.GetPlayers())
        {
            if (p == null || !p.IsValid || IsBot(p) || !HasSteamId(p)) continue;
            _api.EnqueueEvent(new PlayerConnectEventDto
            {
                SteamId     = (long)SteamId(p),
                DisplayName = p.PlayerName,
            });
        }
    }

    private string CurrentMapName()
    {
        var bspName = Server.MapName;
        try
        {
            var workshopDir = Path.Combine(_gameDir, "maps", "workshop");
            if (Directory.Exists(workshopDir))
            {
                foreach (var dir in Directory.EnumerateDirectories(workshopDir))
                {
                    if (File.Exists(Path.Combine(dir, bspName + ".bsp")))
                        return $"workshop/{Path.GetFileName(dir)}/{bspName}";
                }
            }
        }
        catch { /* non-critical */ }
        return bspName;
    }

    private HookResult OnPlayerConnect(EventPlayerConnectFull @event, GameEventInfo _)
    {
        var p = @event.Userid;
        if (p == null || !p.IsValid || IsBot(p)) return HookResult.Continue;
        var sid = SteamId(p);
        if (sid == 0UL) return HookResult.Continue;
        _api.EnqueueEvent(new PlayerConnectEventDto
        {
            SteamId     = (long)sid,
            DisplayName = p.PlayerName,
        });
        return HookResult.Continue;
    }

    private HookResult OnPlayerTeam(EventPlayerTeam @event, GameEventInfo _)
    {
        var p = @event.Userid;
        if (p == null || !p.IsValid || IsBot(p)) return HookResult.Continue;
        var sid = SteamId(p);
        // Team 3 = CT, Team 2 = T, Team 0 = Unassigned, Team 1 = Spectator
        if (@event.Team is 2 or 3)
            _playerTeams[sid] = @event.Team == 3 ? "CT" : "T";
        else
            _playerTeams.Remove(sid);
        return HookResult.Continue;
    }

    private HookResult OnRoundMvp(EventRoundMvp @event, GameEventInfo _)
    {
        if (_matchId == string.Empty || IsWarmup()) return HookResult.Continue;
        var p = @event.Userid;
        if (p == null || !p.IsValid || IsBot(p) || !HasSteamId(p)) return HookResult.Continue;
        var sid = SteamId(p);
        _playerMvps[sid] = _playerMvps.GetValueOrDefault(sid) + 1;
        _api.EnqueueEvent(new MvpEventDto
        {
            MatchId     = _matchId,
            RoundNumber = _currentRound,
            SteamId     = (long)sid,
            Reason      = @event.Reason,
        });
        return HookResult.Continue;
    }

    private HookResult OnPlayerDeath(EventPlayerDeath @event, GameEventInfo _)
    {
        if (_matchId == string.Empty || IsWarmup()) return HookResult.Continue;
        var victim = @event.Userid;
        var killer = @event.Attacker;
        Logger.LogInformation("[CB] OnPlayerDeath victim={Victim}(bot={VBot},slot={VSlot},sid={VSid}) killer={Killer}(bot={KBot},slot={KSlot},sid={KSid}) weapon={Weapon}",
            victim?.PlayerName, victim?.IsBot, victim?.Slot, victim != null ? SteamId(victim) : 0,
            killer?.PlayerName, killer?.IsBot, killer?.Slot, killer != null ? SteamId(killer) : 0,
            @event.Weapon);
        if (victim == null || !victim.IsValid || IsBot(victim) || !HasSteamId(victim)) return HookResult.Continue;
        var assister = @event.Assister;
        _api.EnqueueEvent(new KillEventDto
        {
            MatchId         = _matchId,
            RoundNumber     = _currentRound,
            KillerSteamId   = killer?.IsValid   == true && !IsBot(killer)   && HasSteamId(killer)   ? (long?)SteamId(killer)   : null,
            VictimSteamId   = (long)SteamId(victim),
            AssisterSteamId = assister?.IsValid == true && !IsBot(assister) && HasSteamId(assister) ? (long?)SteamId(assister) : null,
            Weapon          = @event.Weapon,
            Headshot        = @event.Headshot,
            Penetrated      = @event.Penetrated > 0,
            Noscope         = @event.Noscope,
            Thrusmoke       = @event.Thrusmoke,
        });
        return HookResult.Continue;
    }

    private HookResult OnPlayerHurt(EventPlayerHurt @event, GameEventInfo _)
    {
        if (_matchId == string.Empty || IsWarmup()) return HookResult.Continue;
        var victim = @event.Userid;
        var attacker = @event.Attacker;
        Logger.LogInformation("[CB] OnPlayerHurt victim={Victim}(bot={VBot},sid={VSid}) attacker={Attacker}(bot={ABot},sid={ASid}) weapon={Weapon} dmg={Dmg}",
            victim?.PlayerName, victim?.IsBot, victim != null ? SteamId(victim) : 0,
            attacker?.PlayerName, attacker?.IsBot, attacker != null ? SteamId(attacker) : 0,
            @event.Weapon, @event.DmgHealth);
        if (victim == null || !victim.IsValid || IsBot(victim) || !HasSteamId(victim)) return HookResult.Continue;
        _api.EnqueueEvent(new DamageEventDto
        {
            MatchId          = _matchId,
            RoundNumber      = _currentRound,
            AttackerSteamId  = attacker?.IsValid == true && !IsBot(attacker) && HasSteamId(attacker) ? (long?)SteamId(attacker) : null,
            VictimSteamId    = (long)SteamId(victim),
            Weapon           = @event.Weapon,
            Damage           = @event.DmgHealth,
            DamageArmor      = @event.DmgArmor,
            Hitgroup         = @event.Hitgroup.ToString(),
        });
        return HookResult.Continue;
    }

    // ── Utility events ────────────────────────────────────────────────────────

    private HookResult OnFlashDetonate(EventFlashbangDetonate @event, GameEventInfo _)
    {
        // Individual player blind durations arrive via EventPlayerBlind — not yet implemented.
        // TODO: Register EventPlayerBlind to emit FlashEventDto per blinded player.
        return HookResult.Continue;
    }

    private HookResult OnSmokeDetonate(EventSmokegrenadeDetonate @event, GameEventInfo _)
    {
        EmitUtility(@event.Userid, "smoke_start");
        return HookResult.Continue;
    }

    private HookResult OnMolotovDetonate(EventMolotovDetonate @event, GameEventInfo _)
    {
        EmitUtility(@event.Userid, "molotov_detonate");
        return HookResult.Continue;
    }

    private HookResult OnHeDetonate(EventHegrenadeDetonate @event, GameEventInfo _)
    {
        EmitUtility(@event.Userid, "he_detonate");
        return HookResult.Continue;
    }

    private void EmitUtility(CCSPlayerController? player, string eventType)
    {
        if (_matchId == string.Empty || IsWarmup() || player == null || !player.IsValid) return;
        _api.EnqueueEvent(new UtilityEventDto
        {
            MatchId     = _matchId,
            RoundNumber = _currentRound,
            SteamId     = (long)SteamId(player),
            EventType   = eventType,
        });
    }

    private HookResult OnWeaponFire(EventWeaponFire @event, GameEventInfo _)
    {
        if (_matchId == string.Empty || IsWarmup()) return HookResult.Continue;
        var p = @event.Userid;
        if (p == null || !p.IsValid) return HookResult.Continue;
        _api.EnqueueEvent(new WeaponFireEventDto
        {
            MatchId     = _matchId,
            RoundNumber = _currentRound,
            SteamId     = (long)SteamId(p),
            Weapon      = @event.Weapon,
        });
        return HookResult.Continue;
    }

    // ── Demo management ───────────────────────────────────────────────────────

    private void PruneOldDemos(int keep)
    {
        var demoDir = Path.Combine(_gameDir, "csgo");
        try
        {
            var demos = Directory.GetFiles(demoDir, "*.dem")
                .OrderBy(File.GetLastWriteTimeUtc)
                .ToArray();
            foreach (var old in demos.Take(Math.Max(0, demos.Length - keep)))
            {
                File.Delete(old);
                Logger.LogInformation("[CB] Deleted old demo: {File}", Path.GetFileName(old));
            }
        }
        catch (Exception ex)
        {
            Logger.LogWarning("[CB] Demo prune failed: {Error}", ex.Message);
        }
    }

    // ── Config ────────────────────────────────────────────────────────────────

    private PluginConfig LoadConfig()
    {
        var path = Path.Combine(ModuleDirectory, "config.json");
        if (!File.Exists(path))
        {
            var defaults = new PluginConfig();
            File.WriteAllText(path, JsonSerializer.Serialize(defaults, new JsonSerializerOptions { WriteIndented = true }));
            return defaults;
        }
        return JsonSerializer.Deserialize<PluginConfig>(File.ReadAllText(path)) ?? new PluginConfig();
    }
}
