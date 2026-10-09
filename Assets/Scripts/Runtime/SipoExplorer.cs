using System;
using UnityEngine;

namespace Sipo
{
    [Serializable]
    public sealed class SipoViewpoint
    {
        public string label = "Central atrium";
        public string description = "Look up. A little wonder is always in season.";
        public Vector3 position;
        public float yaw;
        public float pitch;
    }

    [Serializable]
    public sealed class SipoDepartmentZone
    {
        public string label = "Central atrium";
        public string description = "A little wonder in every aisle.";
        public Bounds bounds;
    }

    /// <summary>Self-contained desktop exploration, directory, and scene viewpoints.</summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(CharacterController))]
    public sealed class SipoExplorer : MonoBehaviour
    {
        [Header("Scene setup")]
        [SerializeField] private Transform view;
        [SerializeField] private Vector3 spawnPosition;
        [SerializeField] private float spawnYaw;
        [SerializeField] private SipoViewpoint[] viewpoints = Array.Empty<SipoViewpoint>();
        [SerializeField] private SipoDepartmentZone[] departments = Array.Empty<SipoDepartmentZone>();
        public Vector2 mapWorldMin = new Vector2(-24, -22);
        public Vector2 mapWorldMax = new Vector2(24, 22);

        [Header("Movement")]
        [Min(0.1f)] public float walkSpeed = 3.3f;
        [Min(0.1f)] public float fastSpeed = 5.7f;
        [Range(0.2f, 5f)] public float mouseSensitivity = 1.65f;
        [Min(0.1f)] public float eyeHeight = 1.62f;
        public float recoveryHeight = -6f;

        private CharacterController controller;
        private Vector3 smoothVelocity;
        private float gravityVelocity;
        private float pitch;
        private float yaw;
        private bool exploring;
        private bool showMap;
        private bool showHelp;
        private bool entered;
        private bool interfaceHidden;
        private float toastUntil;
        private string toast;
        private string location = "Central atrium";
        private string locationDescription = "A little wonder in every aisle.";
        private int activeViewpoint = -1;
        private Texture2D rounded;
        private Texture2D softRounded;
        private GUIStyle titleStyle, labelStyle, smallStyle, tinyStyle, brandStyle, buttonStyle;
        private static readonly Color Ink = new Color(0.055f, 0.09f, 0.17f, 0.95f);
        private static readonly Color SoftInk = new Color(0.065f, 0.095f, 0.17f, 0.86f);
        private static readonly Color Orange = new Color(1f, 0.37f, 0.12f);
        private static readonly Color Muted = new Color(0.75f, 0.81f, 0.89f);
        private static readonly Color Cream = new Color(1f, 0.95f, 0.85f);

        public void Configure(Transform cameraTransform, Vector3 spawn, float initialYaw,
            SipoViewpoint[] scenicViewpoints, SipoDepartmentZone[] zones)
        {
            view = cameraTransform;
            spawnPosition = spawn;
            spawnYaw = initialYaw;
            viewpoints = scenicViewpoints ?? Array.Empty<SipoViewpoint>();
            departments = zones ?? Array.Empty<SipoDepartmentZone>();
            transform.SetPositionAndRotation(spawnPosition, Quaternion.Euler(0, spawnYaw, 0));
            if (view != null)
            {
                view.localPosition = Vector3.up * eyeHeight;
                view.localRotation = Quaternion.identity;
            }
            yaw = spawnYaw;
            pitch = 0;
        }

        private void Awake()
        {
            controller = GetComponent<CharacterController>();
            if (view == null)
            {
                Camera childCamera = GetComponentInChildren<Camera>();
                if (childCamera != null) view = childCamera.transform;
            }
            yaw = spawnYaw;
            if (view != null) view.localPosition = Vector3.up * eyeHeight;
            controller.minMoveDistance = 0;
            controller.skinWidth = 0.025f;
            controller.stepOffset = 0.3f;
            controller.slopeLimit = 48;
            SetExploring(false);
        }

        private void Start()
        {
            Teleport(spawnPosition, spawnYaw, 0, false);
            UpdateLocation();
        }

        private void OnDisable()
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        private void OnDestroy()
        {
            if (rounded != null) Destroy(rounded);
            if (softRounded != null) Destroy(softRounded);
        }

        private void OnApplicationFocus(bool hasFocus)
        {
            if (!hasFocus) SetExploring(false);
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (showMap || showHelp)
                {
                    showMap = false;
                    showHelp = false;
                    SetExploring(true);
                }
                else SetExploring(!exploring);
            }
            if (Input.GetKeyDown(KeyCode.M)) ToggleMap();
            if (Input.GetKeyDown(KeyCode.H) || Input.GetKeyDown(KeyCode.F1)) ToggleHelp();
            if (Input.GetKeyDown(KeyCode.F2)) interfaceHidden = !interfaceHidden;
            if (Input.GetKeyDown(KeyCode.Home)) ReturnToEntrance();
            for (int i = 0; i < Mathf.Min(9, viewpoints.Length); i++)
                if (Input.GetKeyDown((KeyCode)((int)KeyCode.Alpha1 + i))) Visit(i);

            if (transform.position.y < recoveryHeight)
            {
                ReturnToEntrance();
                Notify("Back on solid ground. Welcome home.");
            }

            if (exploring && view != null)
            {
                yaw += Input.GetAxisRaw("Mouse X") * mouseSensitivity;
                pitch = Mathf.Clamp(pitch - Input.GetAxisRaw("Mouse Y") * mouseSensitivity, -76, 76);
                transform.rotation = Quaternion.Euler(0, yaw, 0);
                view.localRotation = Quaternion.Euler(pitch, 0, 0);
                float forward = Axis(KeyCode.W, KeyCode.UpArrow, KeyCode.S, KeyCode.DownArrow);
                float side = Axis(KeyCode.D, KeyCode.RightArrow, KeyCode.A, KeyCode.LeftArrow);
                Vector3 input = Vector3.ClampMagnitude(new Vector3(side, 0, forward), 1);
                float speed = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift) ? fastSpeed : walkSpeed;
                Vector3 desired = transform.TransformDirection(input) * speed;
                smoothVelocity = Vector3.Lerp(smoothVelocity, desired, 1 - Mathf.Exp(-15 * Time.deltaTime));
            }
            else smoothVelocity = Vector3.zero;

            // Gravity remains active in menus, but cannot accumulate while resting on a floor.
            if (controller.isGrounded && gravityVelocity < 0) gravityVelocity = -2f;
            gravityVelocity = Mathf.Max(gravityVelocity - 22f * Time.deltaTime, -35);
            if (controller.enabled)
                controller.Move((smoothVelocity + Vector3.up * gravityVelocity) * Mathf.Min(Time.deltaTime, 0.05f));
            UpdateLocation();
        }

        private static float Axis(KeyCode positive, KeyCode positiveAlt, KeyCode negative, KeyCode negativeAlt)
        {
            return ((Input.GetKey(positive) || Input.GetKey(positiveAlt)) ? 1 : 0)
                - ((Input.GetKey(negative) || Input.GetKey(negativeAlt)) ? 1 : 0);
        }

        private void UpdateLocation()
        {
            location = "Central atrium";
            locationDescription = "A little wonder in every aisle.";
            float smallest = float.PositiveInfinity;
            foreach (SipoDepartmentZone zone in departments)
            {
                if (zone == null || !zone.bounds.Contains(transform.position + Vector3.up * 0.5f)) continue;
                float volume = zone.bounds.size.x * zone.bounds.size.y * zone.bounds.size.z;
                if (volume >= smallest) continue;
                smallest = volume;
                location = zone.label;
                locationDescription = zone.description;
            }
        }

        private void SetExploring(bool value)
        {
            exploring = value;
            if (value)
            {
                entered = true;
                showMap = false;
                showHelp = false;
            }
            Cursor.lockState = value ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !value;
        }

        private void ToggleMap()
        {
            bool next = !showMap;
            SetExploring(!next);
            showMap = next;
            showHelp = false;
        }

        private void ToggleHelp()
        {
            bool next = !showHelp;
            SetExploring(!next);
            showHelp = next;
            showMap = false;
        }

        private void ReturnToEntrance()
        {
            Teleport(spawnPosition, spawnYaw, 0, true);
            activeViewpoint = -1;
            Notify("The grand entrance");
        }

        private void Visit(int index)
        {
            if (index < 0 || index >= viewpoints.Length || viewpoints[index] == null) return;
            SipoViewpoint point = viewpoints[index];
            if (!Teleport(point.position, point.yaw, point.pitch, true)) return;
            activeViewpoint = index;
            Notify(point.label + "  /  " + point.description);
        }

        private bool Teleport(Vector3 target, float targetYaw, float targetPitch, bool resume)
        {
            if (controller == null) controller = GetComponent<CharacterController>();
            bool wasEnabled = controller.enabled;
            controller.enabled = false;
            Physics.SyncTransforms();
            if (!FindStandingPosition(target, out Vector3 safe))
            {
                controller.enabled = wasEnabled;
                Notify("That viewpoint is blocked. Try another stop on the directory.");
                return false;
            }
            transform.SetPositionAndRotation(safe, Quaternion.Euler(0, targetYaw, 0));
            yaw = targetYaw;
            pitch = Mathf.Clamp(targetPitch, -76, 76);
            if (view != null) view.localRotation = Quaternion.Euler(pitch, 0, 0);
            gravityVelocity = -2;
            smoothVelocity = Vector3.zero;
            controller.enabled = wasEnabled;
            if (resume) SetExploring(true);
            UpdateLocation();
            return true;
        }

        private bool FindStandingPosition(Vector3 target, out Vector3 result)
        {
            float radius = controller.radius;
            float height = controller.height;
            // Usually the first authored position succeeds; nearby samples recover from local obstructions.
            for (int attempt = 0; attempt < 25; attempt++)
            {
                Vector3 candidate = target;
                if (attempt > 0)
                {
                    float angle = (attempt - 1) * 45 * Mathf.Deg2Rad;
                    float distance = 0.8f * (1 + (attempt - 1) / 8);
                    candidate += new Vector3(Mathf.Sin(angle), 0, Mathf.Cos(angle)) * distance;
                }
                if (!Physics.Raycast(candidate + Vector3.up * 0.55f, Vector3.down,
                    out RaycastHit floor, 2f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore)) continue;
                if (Vector3.Dot(floor.normal, Vector3.up) < 0.66f) continue;
                candidate.y = floor.point.y + 0.04f;
                Vector3 bottom = candidate + Vector3.up * (radius + 0.035f);
                Vector3 top = candidate + Vector3.up * (height - radius);
                if (Physics.CheckCapsule(bottom, top, radius, Physics.DefaultRaycastLayers,
                    QueryTriggerInteraction.Ignore)) continue;
                result = candidate;
                return true;
            }
            result = target;
            return false;
        }

        private void Notify(string message)
        {
            toast = message;
            toastUntil = Time.unscaledTime + 4.5f;
        }

        private void EnsureStyles()
        {
            if (rounded != null) return;
            rounded = RoundTexture(32, 9);
            softRounded = RoundTexture(32, 5);
            titleStyle = new GUIStyle(GUI.skin.label) { fontSize = 29, fontStyle = FontStyle.Bold, wordWrap = true };
            titleStyle.normal.textColor = Cream;
            labelStyle = new GUIStyle(GUI.skin.label) { fontSize = 16, wordWrap = true };
            labelStyle.normal.textColor = Color.white;
            smallStyle = new GUIStyle(GUI.skin.label) { fontSize = 13, wordWrap = true };
            smallStyle.normal.textColor = Muted;
            tinyStyle = new GUIStyle(GUI.skin.label) { fontSize = 10, fontStyle = FontStyle.Bold };
            tinyStyle.normal.textColor = Muted;
            brandStyle = new GUIStyle(GUI.skin.label) { fontSize = 32, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
            brandStyle.normal.textColor = Color.white;
            buttonStyle = new GUIStyle(GUI.skin.button)
            {
                fontSize = 15, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleLeft,
                padding = new RectOffset(16, 12, 8, 8), border = new RectOffset(9, 9, 9, 9)
            };
            buttonStyle.normal.background = rounded;
            buttonStyle.hover.background = rounded;
            buttonStyle.active.background = rounded;
            buttonStyle.focused.background = rounded;
            buttonStyle.normal.textColor = Color.white;
            buttonStyle.hover.textColor = Color.white;
            buttonStyle.active.textColor = Color.white;
            buttonStyle.focused.textColor = Color.white;
        }

        private static Texture2D RoundTexture(int size, int radius)
        {
            Texture2D texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
            texture.name = "Sipo UI";
            texture.hideFlags = HideFlags.HideAndDontSave;
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float nearestX = Mathf.Clamp(x, radius, size - radius - 1);
                    float nearestY = Mathf.Clamp(y, radius, size - radius - 1);
                    float distance = Vector2.Distance(new Vector2(x, y), new Vector2(nearestX, nearestY));
                    texture.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(radius - distance + 0.5f)));
                }
            texture.Apply(false, true);
            return texture;
        }

        private void OnGUI()
        {
            EnsureStyles();
            float scale = Mathf.Clamp(Mathf.Min(Screen.width / 1440f, Screen.height / 900f), 0.55f, 1.65f);
            Matrix4x4 previous = GUI.matrix;
            GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(scale, scale, 1));
            float width = Screen.width / scale;
            float height = Screen.height / scale;

            if (!interfaceHidden || !exploring)
            {
                DrawBrand();
                DrawLocation(width);
                if (exploring)
                {
                    DrawBottomBar(width, height);
                    Color previousColor = GUI.color;
                    GUI.color = new Color(1, 1, 1, 0.65f);
                    GUI.DrawTexture(new Rect(width / 2 - 1.5f, height / 2 - 1.5f, 3, 3), rounded);
                    GUI.color = previousColor;
                }
            }

            if (!exploring)
            {
                Solid(new Rect(0, 0, width, height), new Color(0.025f, 0.04f, 0.08f, 0.35f));
                if (showMap) DrawMap(width, height);
                else if (showHelp) DrawHelp(width, height);
                else DrawWelcome(width, height);
            }
            if (exploring && !interfaceHidden && Time.unscaledTime < toastUntil && !string.IsNullOrEmpty(toast))
            {
                float toastWidth = Mathf.Min(760, width - 100);
                Panel(new Rect((width - toastWidth) / 2, height - 132, toastWidth, 56), SoftInk);
                GUIStyle centered = new GUIStyle(smallStyle) { alignment = TextAnchor.MiddleCenter };
                GUI.Label(new Rect((width - toastWidth) / 2 + 18, height - 129, toastWidth - 36, 48), toast, centered);
            }
            GUI.matrix = previous;
        }

        private void DrawBrand()
        {
            Panel(new Rect(28, 25, 111, 55), Orange);
            GUI.Label(new Rect(30, 25, 107, 52), "SIPO", brandStyle);
            Panel(new Rect(147, 25, 212, 55), SoftInk);
            GUI.Label(new Rect(163, 36, 185, 18), "A WORLD OF EVERYDAY JOY", tinyStyle);
            GUI.Label(new Rect(163, 53, 185, 20), "The supermarket experience", smallStyle);
        }

        private void DrawLocation(float width)
        {
            Panel(new Rect(width - 321, 25, 293, 65), SoftInk);
            GUI.Label(new Rect(width - 301, 36, 253, 18), "YOU ARE EXPLORING", tinyStyle);
            GUI.Label(new Rect(width - 301, 54, 253, 28), location, labelStyle);
        }

        private void DrawBottomBar(float width, float height)
        {
            Panel(new Rect(28, height - 67, 407, 40), SoftInk);
            GUI.Label(new Rect(44, height - 57, 380, 23), "WASD  Walk     M  Directory     H  Help     ESC  Menu", smallStyle);
            GUIStyle right = new GUIStyle(tinyStyle) { alignment = TextAnchor.MiddleRight };
            GUI.Label(new Rect(width - 260, height - 60, 231, 25), "TAKE YOUR TIME. LOOK AROUND.", right);
        }

        private void DrawWelcome(float width, float height)
        {
            float panelWidth = Mathf.Min(514, width - 50);
            float panelHeight = 465;
            Rect rect = new Rect((width - panelWidth) / 2, (height - panelHeight) / 2 + 20, panelWidth, panelHeight);
            Panel(rect, Ink);
            Solid(new Rect(rect.x + 28, rect.y + 29, 40, 4), Orange);
            GUI.Label(new Rect(rect.x + 28, rect.y + 48, panelWidth - 56, 24), "WELCOME TO SIPO", tinyStyle);
            GUI.Label(new Rect(rect.x + 28, rect.y + 77, panelWidth - 56, 84), entered ? "A little pause.\nA lot to discover." : "Every aisle,\na little adventure.", titleStyle);
            GUI.Label(new Rect(rect.x + 29, rect.y + 174, panelWidth - 58, 65),
                "Step into a joyful world of fresh discoveries, warm lights and everyday wonder. This space is yours to explore.", labelStyle);
            if (Button(new Rect(rect.x + 28, rect.y + 260, panelWidth - 56, 49), entered ? "Continue exploring   →" : "Enter the supermarket   →", Orange)) SetExploring(true);
            if (Button(new Rect(rect.x + 28, rect.y + 320, (panelWidth - 68) / 2, 46), "Store directory", new Color(0.15f, 0.21f, 0.31f))) ToggleMap();
            if (Button(new Rect(rect.center.x + 6, rect.y + 320, (panelWidth - 68) / 2, 46), "How to explore", new Color(0.15f, 0.21f, 0.31f))) ToggleHelp();
            GUI.Label(new Rect(rect.x + 29, rect.y + 390, panelWidth - 58, 42), "Mouse to look around   •   WASD or arrows to walk\nPress Escape anytime to release your cursor.", smallStyle);
        }

        private void DrawHelp(float width, float height)
        {
            float panelWidth = Mathf.Min(610, width - 50);
            float panelHeight = 522;
            Rect rect = new Rect((width - panelWidth) / 2, (height - panelHeight) / 2 + 20, panelWidth, panelHeight);
            Panel(rect, Ink);
            GUI.Label(new Rect(rect.x + 28, rect.y + 24, panelWidth - 56, 40), "Make yourself at home.", titleStyle);
            GUI.Label(new Rect(rect.x + 29, rect.y + 73, panelWidth - 58, 28), "Everything you need for a leisurely look around.", smallStyle);
            string[] keys = { "W A S D  /  ARROWS", "MOUSE", "SHIFT", "M", "1 — 9", "HOME", "H  /  F1", "F2", "ESC" };
            string[] actions = { "Walk through the supermarket", "Look around", "Walk a little faster", "Open the store directory", "Visit a scenic viewpoint", "Return to the entrance", "Show these controls", "Hide or show the interface", "Pause and release your cursor" };
            for (int i = 0; i < keys.Length; i++)
            {
                float y = rect.y + 121 + i * 32;
                GUI.Label(new Rect(rect.x + 30, y, 167, 25), keys[i], tinyStyle);
                GUI.Label(new Rect(rect.x + 200, y - 2, panelWidth - 225, 28), actions[i], smallStyle);
            }
            if (Button(new Rect(rect.x + 28, rect.y + panelHeight - 77, panelWidth - 56, 48), "Back to exploring   →", Orange)) SetExploring(true);
        }

        private void DrawMap(float width, float height)
        {
            float panelWidth = Mathf.Min(1050, width - 56);
            float panelHeight = Mathf.Min(636, height - 130);
            Rect rect = new Rect((width - panelWidth) / 2, (height - panelHeight) / 2 + 22, panelWidth, panelHeight);
            Panel(rect, Ink);
            GUI.Label(new Rect(rect.x + 26, rect.y + 22, panelWidth - 60, 41), "Good things, this way.", titleStyle);
            GUI.Label(new Rect(rect.x + 27, rect.y + 67, panelWidth - 60, 26), "Explore the directory. Choose a viewpoint to visit.", smallStyle);
            float mapWidth = Mathf.Min(510, panelWidth * 0.52f);
            Rect map = new Rect(rect.x + 27, rect.y + 116, mapWidth, panelHeight - 196);
            Panel(map, new Color(0.11f, 0.17f, 0.26f));
            Rect interior = new Rect(map.x + 20, map.y + 20, map.width - 40, map.height - 40);
            for (int i = 1; i < 6; i++)
            {
                Solid(new Rect(interior.x + interior.width * i / 6, interior.y, 1, interior.height), new Color(1, 1, 1, 0.05f));
                Solid(new Rect(interior.x, interior.y + interior.height * i / 6, interior.width, 1), new Color(1, 1, 1, 0.05f));
            }
            foreach (SipoDepartmentZone zone in departments)
            {
                if (zone == null) continue;
                Vector2 a = MapPoint(zone.bounds.min, interior);
                Vector2 b = MapPoint(zone.bounds.max, interior);
                Rect zoneRect = Rect.MinMaxRect(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y), Mathf.Max(a.x, b.x), Mathf.Max(a.y, b.y));
                Panel(zoneRect, new Color(0.28f, 0.46f, 0.5f, 0.32f));
            }
            GUIStyle mapNumber = new GUIStyle(tinyStyle) { alignment = TextAnchor.MiddleCenter };
            mapNumber.normal.textColor = Color.white;
            for (int i = 0; i < viewpoints.Length; i++)
            {
                if (viewpoints[i] == null) continue;
                Vector2 p = MapPoint(viewpoints[i].position, interior);
                Rect pin = new Rect(p.x - 13, p.y - 13, 26, 26);
                Panel(pin, i == activeViewpoint ? Orange : new Color(0.16f, 0.35f, 0.47f));
                GUI.Label(pin, (i + 1).ToString(), mapNumber);
                if (GUI.Button(pin, GUIContent.none, GUIStyle.none)) Visit(i);
            }
            Vector2 player = MapPoint(transform.position, interior);
            Panel(new Rect(player.x - 7, player.y - 7, 14, 14), Cream);
            GUI.Label(new Rect(player.x + 9, player.y - 9, 95, 25), "YOU", tinyStyle);

            float listX = map.xMax + 23;
            float listWidth = rect.xMax - listX - 27;
            int count = Mathf.Min(9, viewpoints.Length);
            float itemHeight = Mathf.Min(48, (panelHeight - 220) / Mathf.Max(1, count));
            if (count == 0)
                GUI.Label(new Rect(listX, map.y + 18, listWidth, 80), "Take a stroll through the atrium and discover each department at your own pace.", labelStyle);
            for (int i = 0; i < count; i++)
            {
                SipoViewpoint point = viewpoints[i];
                if (point == null) continue;
                if (Button(new Rect(listX, map.y + i * (itemHeight + 4), listWidth, itemHeight), (i + 1) + "   " + point.label,
                    new Color(0.14f, 0.21f, 0.31f))) Visit(i);
            }
            if (Button(new Rect(rect.x + 27, rect.yMax - 60, mapWidth, 37), "Continue exploring   →", Orange)) SetExploring(true);
            GUI.Label(new Rect(listX, rect.yMax - 55, listWidth, 30), "HOME  Return to the grand entrance", tinyStyle);
        }

        private Vector2 MapPoint(Vector3 world, Rect rect)
        {
            float x = Mathf.InverseLerp(mapWorldMin.x, mapWorldMax.x, world.x);
            float y = Mathf.InverseLerp(mapWorldMin.y, mapWorldMax.y, world.z);
            return new Vector2(rect.x + Mathf.Clamp01(x) * rect.width, rect.y + Mathf.Clamp01(y) * rect.height);
        }

        private void Panel(Rect rect, Color color)
        {
            Color previous = GUI.color;
            GUI.color = color;
            GUI.DrawTexture(rect, rect.width < 40 ? softRounded : rounded);
            GUI.color = previous;
        }

        private static void Solid(Rect rect, Color color)
        {
            Color previous = GUI.color;
            GUI.color = color;
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            GUI.color = previous;
        }

        private bool Button(Rect rect, string text, Color color)
        {
            Color previous = GUI.backgroundColor;
            GUI.backgroundColor = rect.Contains(Event.current.mousePosition) ? Color.Lerp(color, Color.white, 0.16f) : color;
            bool pressed = GUI.Button(rect, text, buttonStyle);
            GUI.backgroundColor = previous;
            return pressed;
        }
    }
}
