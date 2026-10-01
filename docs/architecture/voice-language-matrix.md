# Voice and language matrix

Text language support and voice support are intentionally separate capabilities.

| Language | Text | Script auto-detect | Browser STT locale | Browser TTS locale | Polly language |
| English | Yes | Yes | en-GB / en-US | en-GB / en-US | Yes |
| Hindi | Yes | Yes | hi-IN | hi-IN | Yes |
| Telugu | Yes | Yes | te-IN | te-IN | Not assumed |
| Tamil | Yes | Yes | ta-IN | ta-IN | Not assumed |
| Bengali | Yes | Yes | bn-IN | bn-IN | Not assumed |
| Kannada | Yes | Yes | kn-IN | kn-IN | Not assumed |
| Marathi | Yes | Yes where script is present | provider/device dependent | provider/device dependent | provider dependent |
| Gujarati | Yes | Yes | provider/device dependent | provider/device dependent | provider dependent |
| Punjabi | Yes | Yes | provider/device dependent | provider/device dependent | provider dependent |
| Urdu | Yes | Partial | ur-PK | ur-PK | provider dependent |
| Arabic | Yes | Partial | ar-SA | ar-SA | Yes |
| Spanish | Yes | No | es-ES | es-ES | Yes |
| French | Yes | No | fr-FR | fr-FR | Yes |
| German | Yes | No | de-DE | de-DE | Yes |
| Italian | Yes | No | it-IT | it-IT | Yes |
| Portuguese | Yes | No | pt-PT | pt-PT | Yes |
| Japanese | Yes | Yes | ja-JP | ja-JP | Yes |
| Chinese | Yes | Yes | zh-CN | zh-CN | Yes |

Browser speech availability depends on the user's browser and installed operating-system voices.

Cloud voice IDs are provider configuration, not hard-coded truth. The project should call the provider capabilities endpoint before enabling a voice in a production UI.
