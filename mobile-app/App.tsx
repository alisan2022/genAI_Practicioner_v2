import { StatusBar } from "expo-status-bar";
import { LinearGradient } from "expo-linear-gradient";
import * as Location from "expo-location";
import { type ReactNode, useEffect, useRef, useState } from "react";
import {
  Animated,
  Easing,
  KeyboardAvoidingView,
  Linking,
  NativeModules,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

type UrgencyLevel = "low" | "medium" | "high";
type FacilityKind = "hospital" | "urgent_care" | "gp" | "pharmacy";
type TransportMode = "ambulance" | "ride_hailing" | "self_travel";
type TrafficLevel = "light" | "moderate" | "heavy" | "unknown";

type RouteMetrics = {
  distance_km: number;
  travel_minutes: number;
  average_speed_kmh: number;
  traffic_level: TrafficLevel;
  source: "road_network" | "distance_heuristic";
};

type Facility = {
  name: string;
  kind: FacilityKind;
  address: string;
  contact: string;
  latitude: number;
  longitude: number;
  estimated_wait_minutes: number;
  route?: RouteMetrics | null;
  suitability_score: number;
};

type KnowledgeCard = {
  id: string;
  title: string;
  source: string;
  category: string;
  snippet: string;
  relevance: number;
};

type TriageResult = {
  urgency: UrgencyLevel;
  summary: string;
  reasoning: string[];
  recommended_actions: string[];
  self_care_advice: string[];
  otc_options: string[];
  facilities: Facility[];
  transport: {
    mode: TransportMode;
    rationale: string;
    eta_minutes?: number;
    confidence: number;
  };
  knowledge_cards: KnowledgeCard[];
  safety_disclaimer: string;
  model: string;
  decision_trace: string[];
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type ConnectionState = "idle" | "checking" | "connected" | "error";

const placeholderApiBaseUrl = "https://your-api-domain.com";
const configuredApiBaseUrl = (process.env.EXPO_PUBLIC_API_BASE_URL || "").trim();
const loopbackApiBaseUrls = ["http://127.0.0.1:8000", "http://localhost:8000"];

const urgencyTheme: Record<
  UrgencyLevel,
  { label: string; tint: string; soft: string; track: string; emphasis: string }
> = {
  low: {
    label: "Low urgency",
    tint: "#177A58",
    soft: "#E7F7EE",
    track: "#BFE9D1",
    emphasis: "#0B5E42",
  },
  medium: {
    label: "Needs timely review",
    tint: "#A66B00",
    soft: "#FFF3DA",
    track: "#F4D69C",
    emphasis: "#895600",
  },
  high: {
    label: "High urgency",
    tint: "#C24733",
    soft: "#FFE7E1",
    track: "#F6B9AE",
    emphasis: "#A53523",
  },
};

const parseOptionalInt = (
  value: string,
  label: string,
  min: number,
  max: number
): { value?: number; error?: string } => {
  const trimmed = value.trim();
  if (!trimmed) return {};

  const parsed = Number(trimmed);
  if (!Number.isInteger(parsed)) {
    return { error: `${label} must be a whole number.` };
  }
  if (parsed < min || parsed > max) {
    return { error: `${label} must be between ${min} and ${max}.` };
  }
  return { value: parsed };
};

const kindLabel = (kind: FacilityKind): string => {
  if (kind === "urgent_care") return "Urgent care";
  if (kind === "gp") return "GP";
  return kind.charAt(0).toUpperCase() + kind.slice(1);
};

const transportLabel = (mode: TransportMode): string => {
  if (mode === "ride_hailing") return "Ride-hailing";
  if (mode === "self_travel") return "Self travel";
  return "Ambulance";
};

const trafficLabel = (trafficLevel: TrafficLevel): string => {
  if (trafficLevel === "heavy") return "Heavy traffic";
  if (trafficLevel === "moderate") return "Moderate traffic";
  if (trafficLevel === "light") return "Light traffic";
  return "Route estimate";
};

const urgencyBarValue: Record<UrgencyLevel, number> = {
  low: 0.34,
  medium: 0.68,
  high: 1,
};

const normaliseBaseUrl = (value: string): string => value.trim().replace(/\/+$/, "");

const metroHost = (): string | null => {
  const scriptURL = (NativeModules.SourceCode as { scriptURL?: string } | undefined)?.scriptURL;
  if (!scriptURL) return null;

  try {
    return new URL(scriptURL).hostname;
  } catch {
    return null;
  }
};

const apiBaseCandidates = (): string[] => {
  const candidates: string[] = [];

  if (configuredApiBaseUrl && configuredApiBaseUrl !== placeholderApiBaseUrl) {
    candidates.push(normaliseBaseUrl(configuredApiBaseUrl));
  }

  const detectedMetroHost = metroHost();
  if (detectedMetroHost) {
    candidates.push(`http://${detectedMetroHost}:8000`);
  }

  candidates.push(...loopbackApiBaseUrls);

  return Array.from(new Set(candidates.map(normaliseBaseUrl).filter(Boolean)));
};

const defaultApiBaseUrl = apiBaseCandidates()[0] || loopbackApiBaseUrls[0];

const buildUberUrl = (facility: Facility): string => {
  const query = [
    ["action", "setPickup"],
    ["pickup", "my_location"],
    ["dropoff[latitude]", String(facility.latitude)],
    ["dropoff[longitude]", String(facility.longitude)],
    ["dropoff[nickname]", facility.name],
    ["dropoff[formatted_address]", facility.address],
  ]
    .map(([key, item]) => `${encodeURIComponent(key)}=${encodeURIComponent(item)}`)
    .join("&");

  return `https://m.uber.com/ul/?${query}`;
};

const buildMapsUrl = (facility: Facility): string => {
  if (Platform.OS === "ios") {
    return `http://maps.apple.com/?ll=${facility.latitude},${facility.longitude}&q=${encodeURIComponent(
      facility.name
    )}`;
  }
  return `geo:${facility.latitude},${facility.longitude}?q=${facility.latitude},${facility.longitude}(${encodeURIComponent(
    facility.name
  )})`;
};

const makeId = (): string => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const Section = ({
  title,
  caption,
  children,
}: {
  title: string;
  caption?: string;
  children: ReactNode;
}) => (
  <View style={styles.section}>
    <Text style={styles.sectionTitle}>{title}</Text>
    {caption ? <Text style={styles.sectionCaption}>{caption}</Text> : null}
    {children}
  </View>
);

const ToggleRow = ({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (next: boolean) => void;
}) => (
  <View style={styles.toggleBlock}>
    <Text style={styles.fieldLabel}>{label}</Text>
    <View style={styles.toggleGroup}>
      <Pressable
        accessibilityRole="button"
        onPress={() => onChange(true)}
        style={[styles.toggleOption, value && styles.toggleOptionActive]}
      >
        <Text style={[styles.toggleOptionText, value && styles.toggleOptionTextActive]}>
          Yes
        </Text>
      </Pressable>
      <Pressable
        accessibilityRole="button"
        onPress={() => onChange(false)}
        style={[styles.toggleOption, !value && styles.toggleOptionActive]}
      >
        <Text style={[styles.toggleOptionText, !value && styles.toggleOptionTextActive]}>
          No
        </Text>
      </Pressable>
    </View>
  </View>
);

const ActionButton = ({
  label,
  onPress,
  disabled,
  muted,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  muted?: boolean;
}) => (
  <Pressable
    accessibilityRole="button"
    onPress={onPress}
    disabled={disabled}
    style={[
      styles.primaryButton,
      muted && styles.secondaryButton,
      disabled && styles.buttonDisabled,
    ]}
  >
    <Text style={[styles.primaryButtonText, muted && styles.secondaryButtonText]}>{label}</Text>
  </Pressable>
);

async function readErrorMessage(response: Response): Promise<string> {
  const raw = (await response.text()).trim();
  if (!raw) return `HTTP ${response.status}`;
  try {
    const parsed = JSON.parse(raw) as { detail?: unknown };
    if (typeof parsed.detail === "string" && parsed.detail.trim()) {
      return parsed.detail.trim();
    }
  } catch {
    return raw;
  }
  return raw;
}

async function fetchWithTimeout(input: string, init?: RequestInit, timeoutMs = 3000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(defaultApiBaseUrl);
  const [connectionState, setConnectionState] = useState<ConnectionState>("idle");
  const [connectionMessage, setConnectionMessage] = useState("Connecting to local service...");

  const [symptoms, setSymptoms] = useState("");
  const [knownConditions, setKnownConditions] = useState("");
  const [ageRaw, setAgeRaw] = useState("");
  const [durationRaw, setDurationRaw] = useState("");
  const [painRaw, setPainRaw] = useState("");
  const [mobilityLimited, setMobilityLimited] = useState(false);
  const [emergencySigns, setEmergencySigns] = useState(false);
  const [useLocation, setUseLocation] = useState(false);
  const [coordinates, setCoordinates] = useState<{ latitude: number; longitude: number } | null>(
    null
  );
  const [locationLabel, setLocationLabel] = useState("Location is off.");

  const [triage, setTriage] = useState<TriageResult | null>(null);
  const [assessmentError, setAssessmentError] = useState("");
  const [isAssessing, setIsAssessing] = useState(false);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatError, setChatError] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);

  const reveal = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(reveal, {
      toValue: 1,
      duration: 500,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();
  }, [reveal]);

  const checkConnection = async (preferredBaseUrl?: string): Promise<string | null> => {
    setConnectionState("checking");
    setConnectionMessage("Connecting to local service...");

    const candidates = Array.from(
      new Set(
        [preferredBaseUrl, apiBaseUrl, ...apiBaseCandidates()]
          .map((value) => (value ? normaliseBaseUrl(value) : ""))
          .filter(Boolean)
      )
    );

    for (const candidate of candidates) {
      try {
        const response = await fetchWithTimeout(`${candidate}/health`, undefined, 2500);
        if (!response.ok) {
          throw new Error(await readErrorMessage(response));
        }

        setApiBaseUrl(candidate);
        setConnectionState("connected");
        setConnectionMessage("Local service is ready.");
        return candidate;
      } catch {
        continue;
      }
    }

    setConnectionState("error");
    setConnectionMessage("Local service is unavailable. Make sure the backend is running on this Mac.");
    return null;
  };

  useEffect(() => {
    void checkConnection(defaultApiBaseUrl);
  }, []);

  const requestLocation = async (): Promise<
    { latitude: number; longitude: number } | null
  > => {
    setLocationLabel("Getting your current location...");
    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== "granted") {
      setUseLocation(false);
      setCoordinates(null);
      setLocationLabel("Location permission was not granted.");
      return null;
    }

    const current = await Location.getCurrentPositionAsync({});
    const next = {
      latitude: current.coords.latitude,
      longitude: current.coords.longitude,
    };
    setUseLocation(true);
    setCoordinates(next);
    setLocationLabel("Using your current location for route and traffic ranking.");
    return next;
  };

  const handleLocationChange = async (next: boolean) => {
    if (!next) {
      setUseLocation(false);
      setCoordinates(null);
      setLocationLabel("Location is off.");
      return;
    }

    await requestLocation();
  };

  const submitAssessment = async () => {
    setAssessmentError("");
    if (!symptoms.trim()) {
      setAssessmentError("Please describe the symptoms first.");
      return;
    }

    const age = parseOptionalInt(ageRaw, "Age", 0, 120);
    const duration = parseOptionalInt(durationRaw, "Duration", 0, 8760);
    const pain = parseOptionalInt(painRaw, "Pain level", 0, 10);

    const firstError = age.error || duration.error || pain.error;
    if (firstError) {
      setAssessmentError(firstError);
      return;
    }

    const activeApiBaseUrl =
      connectionState === "connected" ? apiBaseUrl : await checkConnection(apiBaseUrl);
    if (!activeApiBaseUrl) {
      setAssessmentError("Local service is unavailable. Please keep the backend running.");
      return;
    }

    let locationCoordinates = coordinates;
    if (useLocation && !locationCoordinates) {
      locationCoordinates = await requestLocation();
    }

    setIsAssessing(true);

    try {
      const response = await fetch(`${activeApiBaseUrl}/ai-triage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symptoms: symptoms.trim(),
          known_conditions: knownConditions
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          age: age.value,
          duration_hours: duration.value,
          pain_level: pain.value,
          mobility_limited: mobilityLimited,
          emergency_signs_confirmed: emergencySigns,
          location_latitude: locationCoordinates?.latitude,
          location_longitude: locationCoordinates?.longitude,
        }),
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const payload = (await response.json()) as TriageResult;
      setTriage(payload);
      setChatMessages([
        {
          id: makeId(),
          role: "assistant",
          content: `${payload.summary}\n\nAsk an urgent follow-up question if you need to.`,
        },
      ]);
    } catch (error) {
      setAssessmentError(
        error instanceof Error ? error.message : "The assessment request could not be completed."
      );
    } finally {
      setIsAssessing(false);
    }
  };

  const sendChatMessage = async () => {
    if (!triage || !chatInput.trim()) return;

    const activeApiBaseUrl =
      connectionState === "connected" ? apiBaseUrl : await checkConnection(apiBaseUrl);
    if (!activeApiBaseUrl) {
      setChatError("Local service is unavailable right now.");
      return;
    }

    const userMessage: ChatMessage = {
      id: makeId(),
      role: "user",
      content: chatInput.trim(),
    };

    const nextMessages = [...chatMessages, userMessage];
    setChatMessages(nextMessages);
    setChatInput("");
    setChatError("");
    setIsSendingChat(true);

    try {
      const response = await fetch(`${activeApiBaseUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          history: nextMessages.slice(-6).map((message) => ({
            role: message.role,
            content: message.content,
          })),
          triage_summary: `${triage.urgency.toUpperCase()}: ${triage.summary}`,
        }),
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const payload = (await response.json()) as { reply?: string };
      const reply =
        typeof payload.reply === "string" && payload.reply.trim()
          ? payload.reply.trim()
          : "I could not generate a follow-up reply just now.";

      setChatMessages((current) => [
        ...current,
        {
          id: makeId(),
          role: "assistant",
          content: reply,
        },
      ]);
    } catch (error) {
      setChatError(error instanceof Error ? error.message : "Chat is unavailable right now.");
    } finally {
      setIsSendingChat(false);
    }
  };

  const resetAssessment = () => {
    setTriage(null);
    setChatMessages([]);
    setChatInput("");
    setAssessmentError("");
    setChatError("");
  };

  const openUber = async (facility: Facility) => {
    await Linking.openURL(buildUberUrl(facility));
  };

  const openMaps = async (facility: Facility) => {
    await Linking.openURL(buildMapsUrl(facility));
  };

  const currentUrgencyTheme = triage ? urgencyTheme[triage.urgency] : urgencyTheme.low;

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <LinearGradient colors={["#F8FBFF", "#EEF4FF", "#F5F7FC"]} style={styles.background}>
        <KeyboardAvoidingView
          style={styles.keyboardContainer}
          behavior={Platform.OS === "ios" ? "padding" : undefined}
        >
          <ScrollView
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            <Animated.View
              style={[
                styles.hero,
                {
                  opacity: reveal,
                  transform: [
                    {
                      translateY: reveal.interpolate({
                        inputRange: [0, 1],
                        outputRange: [16, 0],
                      }),
                    },
                  ],
                },
              ]}
            >
              <Text style={styles.eyebrow}>GenAI Practitioner</Text>
              <Text style={styles.heroTitle}>GenAI Practitioner</Text>
              <Text style={styles.heroBody}>
                Triage, retrieval, road routing, and urgent follow-up in one care-navigation system.
              </Text>
              <View style={styles.heroPills}>
                <View style={styles.heroPill}>
                  <Text style={styles.heroPillText}>Triage</Text>
                </View>
                <View style={styles.heroPill}>
                  <Text style={styles.heroPillText}>Retrieval</Text>
                </View>
                <View style={styles.heroPill}>
                  <Text style={styles.heroPillText}>Road routing</Text>
                </View>
                <View style={styles.heroPill}>
                  <Text style={styles.heroPillText}>Urgent Q&A</Text>
                </View>
              </View>
              <View style={styles.serviceStatus}>
                <View style={styles.connectionStatus}>
                  <View
                    style={[
                      styles.connectionDot,
                      connectionState === "connected"
                        ? styles.connectionDotSuccess
                        : connectionState === "error"
                        ? styles.connectionDotError
                        : styles.connectionDotIdle,
                    ]}
                  />
                  <Text style={styles.connectionText}>{connectionMessage}</Text>
                </View>
                {connectionState !== "connected" ? (
                  <ActionButton
                    label={connectionState === "checking" ? "Connecting..." : "Retry"}
                    onPress={() => {
                      void checkConnection(apiBaseUrl);
                    }}
                    muted
                    disabled={connectionState === "checking"}
                  />
                ) : null}
              </View>
            </Animated.View>

            {!triage ? (
              <>
                <Section title="Symptoms">
                  <TextInput
                    value={symptoms}
                    onChangeText={setSymptoms}
                    placeholder="Example: Fever, sore throat, and headache since yesterday evening."
                    multiline
                    textAlignVertical="top"
                    style={[styles.input, styles.largeInput]}
                  />
                </Section>

                <Section title="Health Details">
                  <Text style={styles.fieldLabel}>Known conditions</Text>
                  <TextInput
                    value={knownConditions}
                    onChangeText={setKnownConditions}
                    placeholder="Example: asthma, diabetes"
                    style={styles.input}
                  />
                  <View style={styles.fieldGrid}>
                    <View style={styles.fieldGridItem}>
                      <Text style={styles.fieldLabel}>Age</Text>
                      <TextInput
                        value={ageRaw}
                        onChangeText={setAgeRaw}
                        keyboardType="number-pad"
                        placeholder="28"
                        style={styles.input}
                      />
                    </View>
                    <View style={styles.fieldGridItem}>
                      <Text style={styles.fieldLabel}>Hours since it started</Text>
                      <TextInput
                        value={durationRaw}
                        onChangeText={setDurationRaw}
                        keyboardType="number-pad"
                        placeholder="24"
                        style={styles.input}
                      />
                    </View>
                  </View>
                  <View style={styles.fieldGrid}>
                    <View style={styles.fieldGridItem}>
                      <Text style={styles.fieldLabel}>Pain level (0-10)</Text>
                      <TextInput
                        value={painRaw}
                        onChangeText={setPainRaw}
                        keyboardType="number-pad"
                        placeholder="4"
                        style={styles.input}
                      />
                    </View>
                  </View>
                </Section>

                <Section title="Safety Checks">
                  <ToggleRow
                    label="Emergency warning signs confirmed?"
                    value={emergencySigns}
                    onChange={setEmergencySigns}
                  />
                  <ToggleRow
                    label="Is mobility limited?"
                    value={mobilityLimited}
                    onChange={setMobilityLimited}
                  />
                  <ToggleRow
                    label="Use my location for route-aware ranking?"
                    value={useLocation}
                    onChange={(next) => {
                      void handleLocationChange(next);
                    }}
                  />
                  <View style={styles.locationRow}>
                    <Text style={styles.locationLabel}>{locationLabel}</Text>
                  </View>
                </Section>

                {assessmentError ? <Text style={styles.errorText}>{assessmentError}</Text> : null}

                <ActionButton
                  label={isAssessing ? "Assessing..." : "Check urgency"}
                  onPress={submitAssessment}
                  disabled={isAssessing}
                />

                <Text style={styles.disclaimerText}>
                  Educational guidance only. This app does not replace a clinician.
                </Text>
              </>
            ) : (
              <>
                <Section title="Assessment">
                  <View style={[styles.urgencyBanner, { backgroundColor: currentUrgencyTheme.soft }]}>
                    <View
                      style={[
                        styles.urgencyBadge,
                        { backgroundColor: currentUrgencyTheme.track, borderColor: currentUrgencyTheme.tint },
                      ]}
                    >
                      <Text style={[styles.urgencyBadgeText, { color: currentUrgencyTheme.emphasis }]}>
                        {currentUrgencyTheme.label}
                      </Text>
                    </View>
                    <View style={styles.urgencyBarTrack}>
                      <View
                        style={[
                          styles.urgencyBarFill,
                          {
                            width: `${urgencyBarValue[triage.urgency] * 100}%`,
                            backgroundColor: currentUrgencyTheme.tint,
                          },
                        ]}
                      />
                    </View>
                    <Text style={styles.summaryText}>{triage.summary}</Text>
                  </View>

                  <Text style={styles.subheading}>Why the app flagged this</Text>
                  {triage.reasoning.map((item) => (
                    <View key={item} style={styles.listRow}>
                      <View style={[styles.listBullet, { backgroundColor: currentUrgencyTheme.tint }]} />
                      <Text style={styles.listText}>{item}</Text>
                    </View>
                  ))}

                  <Text style={styles.subheading}>Recommended next steps</Text>
                  {triage.recommended_actions.map((item) => (
                    <View key={item} style={styles.listRow}>
                      <View style={[styles.listBullet, { backgroundColor: currentUrgencyTheme.tint }]} />
                      <Text style={styles.listText}>{item}</Text>
                    </View>
                  ))}
                </Section>

                <Section title="Transport">
                  <View style={styles.transportCard}>
                    <View style={styles.transportHeader}>
                      <Text style={styles.transportMode}>{transportLabel(triage.transport.mode)}</Text>
                      <Text style={styles.transportConfidence}>
                        Confidence {Math.round(triage.transport.confidence * 100)}%
                      </Text>
                    </View>
                    <Text style={styles.transportBody}>{triage.transport.rationale}</Text>
                    {typeof triage.transport.eta_minutes === "number" ? (
                      <Text style={styles.transportEta}>Estimated travel time: {triage.transport.eta_minutes} min</Text>
                    ) : null}
                    {triage.facilities[0]?.route ? (
                      <Text style={styles.transportEta}>
                        Best current route: {triage.facilities[0].route.distance_km.toFixed(1)} km at{" "}
                        {Math.round(triage.facilities[0].route.average_speed_kmh)} km/h
                      </Text>
                    ) : null}
                  </View>
                </Section>

                {triage.self_care_advice.length > 0 || triage.otc_options.length > 0 ? (
                  <Section title="Self-Care">
                    {triage.self_care_advice.map((item) => (
                      <View key={item} style={styles.listRow}>
                        <View style={styles.listBulletSoft} />
                        <Text style={styles.listText}>{item}</Text>
                      </View>
                    ))}
                    {triage.otc_options.length > 0 ? (
                      <>
                        <Text style={styles.subheading}>Possible over-the-counter options</Text>
                        <View style={styles.chipWrap}>
                          {triage.otc_options.map((item) => (
                            <View key={item} style={styles.chip}>
                              <Text style={styles.chipText}>{item}</Text>
                            </View>
                          ))}
                        </View>
                      </>
                    ) : null}
                  </Section>
                ) : null}

                <Section title="Nearby Care">
                  {triage.facilities.map((facility) => (
                    <View key={`${facility.name}-${facility.kind}`} style={styles.facilityCard}>
                      <View style={styles.facilityHeader}>
                        <View style={styles.facilityMeta}>
                          <Text style={styles.facilityName}>{facility.name}</Text>
                          <Text style={styles.facilityKind}>{kindLabel(facility.kind)}</Text>
                        </View>
                        <Text style={styles.waitText}>{Math.round(facility.suitability_score * 100)}% fit</Text>
                      </View>
                      <Text style={styles.facilityText}>{facility.address}</Text>
                      <Text style={styles.facilityText}>{facility.contact}</Text>
                      <View style={styles.facilityMetrics}>
                        <View style={styles.metricChip}>
                          <Text style={styles.metricChipText}>Wait {facility.estimated_wait_minutes}m</Text>
                        </View>
                        {facility.route ? (
                          <>
                            <View style={styles.metricChip}>
                              <Text style={styles.metricChipText}>{facility.route.travel_minutes}m drive</Text>
                            </View>
                            <View style={styles.metricChip}>
                              <Text style={styles.metricChipText}>{facility.route.distance_km.toFixed(1)} km</Text>
                            </View>
                            <View style={styles.metricChip}>
                              <Text style={styles.metricChipText}>
                                {trafficLabel(facility.route.traffic_level)}
                              </Text>
                            </View>
                            <View style={styles.metricChip}>
                              <Text style={styles.metricChipText}>
                                {Math.round(facility.route.average_speed_kmh)} km/h
                              </Text>
                            </View>
                          </>
                        ) : null}
                      </View>
                      <View style={styles.actionRow}>
                        <ActionButton label="Uber" onPress={() => openUber(facility)} />
                        <ActionButton label="Maps" onPress={() => openMaps(facility)} muted />
                      </View>
                    </View>
                  ))}
                </Section>

                <Section title="Retrieval Layer">
                  {triage.knowledge_cards.map((card) => (
                    <View key={card.id} style={styles.knowledgeCard}>
                      <View style={styles.knowledgeHeader}>
                        <Text style={styles.knowledgeTitle}>{card.title}</Text>
                        <Text style={styles.knowledgeSource}>{card.source}</Text>
                      </View>
                      <Text style={styles.knowledgeBody}>{card.snippet}</Text>
                    </View>
                  ))}
                </Section>

                <Section title="Urgent Questions">
                  <View style={styles.chatThread}>
                    {chatMessages.map((message) => (
                      <View
                        key={message.id}
                        style={[
                          styles.chatBubble,
                          message.role === "user" ? styles.chatBubbleUser : styles.chatBubbleAssistant,
                        ]}
                      >
                        <Text
                          style={[
                            styles.chatBubbleText,
                            message.role === "user" && styles.chatBubbleTextUser,
                          ]}
                        >
                          {message.content}
                        </Text>
                      </View>
                    ))}
                  </View>
                  <TextInput
                    value={chatInput}
                    onChangeText={setChatInput}
                    placeholder="Example: Should I go tonight if this gets worse?"
                    multiline
                    textAlignVertical="top"
                    style={[styles.input, styles.chatInput]}
                  />
                  {chatError ? <Text style={styles.errorText}>{chatError}</Text> : null}
                  <ActionButton
                    label={isSendingChat ? "Sending..." : "Ask now"}
                    onPress={sendChatMessage}
                    disabled={isSendingChat || !chatInput.trim()}
                    muted
                  />
                </Section>

                <Section title="Safety Note">
                  <Text style={styles.disclaimerBlock}>{triage.safety_disclaimer}</Text>
                </Section>

                <ActionButton label="Start a new assessment" onPress={resetAssessment} />
              </>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F7FBFF",
  },
  background: {
    flex: 1,
  },
  keyboardContainer: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 18,
    paddingTop: 12,
    paddingBottom: 40,
    gap: 16,
  },
  hero: {
    borderRadius: 28,
    padding: 22,
    backgroundColor: "rgba(255,255,255,0.82)",
    borderWidth: 1,
    borderColor: "rgba(160,182,214,0.32)",
  },
  eyebrow: {
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 1.1,
    textTransform: "uppercase",
    color: "#55779B",
  },
  heroTitle: {
    marginTop: 10,
    fontSize: 32,
    lineHeight: 38,
    fontWeight: "700",
    color: "#10253E",
  },
  heroBody: {
    marginTop: 12,
    fontSize: 16,
    lineHeight: 24,
    color: "#4A617B",
  },
  heroPills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 18,
  },
  serviceStatus: {
    marginTop: 18,
    gap: 12,
  },
  heroPill: {
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: "#EEF4FF",
  },
  heroPillText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1C4D80",
  },
  section: {
    padding: 18,
    borderRadius: 24,
    backgroundColor: "rgba(255,255,255,0.9)",
    borderWidth: 1,
    borderColor: "#E2EBF5",
    gap: 12,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#0F2740",
  },
  sectionCaption: {
    fontSize: 15,
    lineHeight: 22,
    color: "#5A7088",
  },
  input: {
    minHeight: 52,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#D5E1EE",
    backgroundColor: "#FBFDFF",
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: "#17304B",
  },
  largeInput: {
    minHeight: 140,
  },
  fieldLabel: {
    fontSize: 15,
    fontWeight: "600",
    color: "#24435F",
  },
  fieldGrid: {
    flexDirection: "row",
    gap: 12,
  },
  fieldGridItem: {
    flex: 1,
    gap: 8,
  },
  toggleBlock: {
    gap: 8,
  },
  toggleGroup: {
    flexDirection: "row",
    gap: 10,
  },
  toggleOption: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 48,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#D6E2EF",
    backgroundColor: "#F9FBFD",
  },
  toggleOptionActive: {
    borderColor: "#245788",
    backgroundColor: "#EEF5FF",
  },
  toggleOptionText: {
    fontSize: 15,
    fontWeight: "600",
    color: "#5C738B",
  },
  toggleOptionTextActive: {
    color: "#15395D",
  },
  locationRow: {
    gap: 10,
  },
  locationLabel: {
    fontSize: 14,
    lineHeight: 20,
    color: "#5A7088",
  },
  primaryButton: {
    minHeight: 54,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0F5BD7",
    paddingHorizontal: 18,
  },
  secondaryButton: {
    backgroundColor: "#EAF2FF",
  },
  buttonDisabled: {
    opacity: 0.55,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  secondaryButtonText: {
    color: "#1A4B80",
  },
  connectionStatus: {
    flex: 1,
    flexDirection: "row",
    gap: 10,
    alignItems: "center",
  },
  connectionDot: {
    width: 10,
    height: 10,
    borderRadius: 99,
  },
  connectionDotSuccess: {
    backgroundColor: "#16A06E",
  },
  connectionDotError: {
    backgroundColor: "#D75A4A",
  },
  connectionDotIdle: {
    backgroundColor: "#9DB1C8",
  },
  connectionText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
    color: "#567089",
  },
  errorText: {
    fontSize: 15,
    lineHeight: 22,
    color: "#B63A29",
  },
  disclaimerText: {
    fontSize: 14,
    lineHeight: 20,
    color: "#5B7189",
    textAlign: "center",
    marginTop: 6,
  },
  urgencyBanner: {
    borderRadius: 20,
    padding: 18,
    gap: 14,
  },
  urgencyBadge: {
    alignSelf: "flex-start",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  urgencyBadgeText: {
    fontSize: 14,
    fontWeight: "700",
  },
  urgencyBarTrack: {
    height: 10,
    borderRadius: 999,
    backgroundColor: "rgba(17,38,61,0.08)",
    overflow: "hidden",
  },
  urgencyBarFill: {
    height: "100%",
    borderRadius: 999,
  },
  summaryText: {
    fontSize: 24,
    lineHeight: 31,
    fontWeight: "700",
    color: "#11263D",
  },
  subheading: {
    marginTop: 2,
    fontSize: 17,
    fontWeight: "700",
    color: "#15304B",
  },
  listRow: {
    flexDirection: "row",
    gap: 10,
    alignItems: "flex-start",
  },
  listBullet: {
    width: 8,
    height: 8,
    borderRadius: 99,
    marginTop: 8,
  },
  listBulletSoft: {
    width: 8,
    height: 8,
    borderRadius: 99,
    marginTop: 8,
    backgroundColor: "#6F8EAE",
  },
  listText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 22,
    color: "#324B65",
  },
  transportCard: {
    borderRadius: 20,
    padding: 16,
    backgroundColor: "#F7FAFF",
    borderWidth: 1,
    borderColor: "#DFEAF6",
    gap: 8,
  },
  transportHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
  },
  transportMode: {
    fontSize: 18,
    fontWeight: "700",
    color: "#143253",
  },
  transportConfidence: {
    fontSize: 14,
    color: "#59718A",
  },
  transportBody: {
    fontSize: 15,
    lineHeight: 22,
    color: "#324B65",
  },
  transportEta: {
    fontSize: 14,
    fontWeight: "600",
    color: "#173E66",
  },
  actionRow: {
    flexDirection: "row",
    gap: 10,
  },
  chipWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: "#EEF4FF",
  },
  chipText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C4D80",
  },
  facilityCard: {
    borderRadius: 18,
    padding: 15,
    backgroundColor: "#FAFCFE",
    borderWidth: 1,
    borderColor: "#E1EAF4",
    gap: 10,
  },
  facilityHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
    alignItems: "flex-start",
  },
  facilityMeta: {
    flex: 1,
    gap: 4,
  },
  facilityName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#17304B",
  },
  facilityKind: {
    fontSize: 13,
    color: "#698097",
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  waitText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#18436F",
  },
  facilityMetrics: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  metricChip: {
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 999,
    backgroundColor: "#EEF4FF",
  },
  metricChipText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#234A74",
  },
  facilityText: {
    fontSize: 14,
    lineHeight: 20,
    color: "#506980",
  },
  knowledgeCard: {
    borderRadius: 18,
    padding: 15,
    backgroundColor: "#FBFDFF",
    borderWidth: 1,
    borderColor: "#E2EBF6",
    gap: 8,
  },
  knowledgeHeader: {
    gap: 4,
  },
  knowledgeTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#17304B",
  },
  knowledgeSource: {
    fontSize: 13,
    color: "#5F7890",
  },
  knowledgeBody: {
    fontSize: 14,
    lineHeight: 21,
    color: "#4A647C",
  },
  chatThread: {
    gap: 10,
  },
  chatBubble: {
    maxWidth: "92%",
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  chatBubbleAssistant: {
    alignSelf: "flex-start",
    backgroundColor: "#F1F6FC",
  },
  chatBubbleUser: {
    alignSelf: "flex-end",
    backgroundColor: "#0F5BD7",
  },
  chatBubbleText: {
    fontSize: 15,
    lineHeight: 22,
    color: "#1F3F5E",
  },
  chatBubbleTextUser: {
    color: "#FFFFFF",
  },
  chatInput: {
    minHeight: 100,
  },
  disclaimerBlock: {
    fontSize: 14,
    lineHeight: 21,
    color: "#556D84",
  },
  traceLabel: {
    marginTop: 4,
    fontSize: 15,
    fontWeight: "700",
    color: "#1C3D60",
  },
  traceText: {
    fontSize: 14,
    lineHeight: 20,
    color: "#597089",
  },
  traceModel: {
    marginTop: 6,
    fontSize: 13,
    color: "#6A829A",
  },
});
