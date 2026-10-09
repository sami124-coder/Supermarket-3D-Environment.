using System;
using UnityEngine;

namespace Sipo
{
    public static class SupermarketPlayerFactory
    {
        /// <summary>Creates a scene-serializable player without requiring an input or UI package.</summary>
        public static GameObject Create(Transform parent, Vector3 spawn, float yaw)
        {
            GameObject player = new GameObject("Sipo Explorer");
            player.transform.SetParent(parent, false);
            player.transform.SetPositionAndRotation(spawn, Quaternion.Euler(0, yaw, 0));
            CharacterController controller = player.AddComponent<CharacterController>();
            controller.height = 1.8f;
            controller.radius = 0.3f;
            controller.center = Vector3.up * 0.9f;
            controller.skinWidth = 0.025f;
            controller.stepOffset = 0.3f;
            controller.slopeLimit = 48;
            GameObject view = new GameObject("Explorer Camera", typeof(Camera), typeof(AudioListener));
            view.tag = "MainCamera";
            view.transform.SetParent(player.transform, false);
            Camera camera = view.GetComponent<Camera>();
            camera.fieldOfView = 70;
            camera.nearClipPlane = 0.06f;
            camera.farClipPlane = 140;
            camera.allowHDR = true;
            camera.allowMSAA = true;
            SipoExplorer explorer = player.AddComponent<SipoExplorer>();
            explorer.Configure(view.transform, spawn, yaw, Array.Empty<SipoViewpoint>(), Array.Empty<SipoDepartmentZone>());
            return player;
        }
    }
}
